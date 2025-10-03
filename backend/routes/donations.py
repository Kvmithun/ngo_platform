import stripe
from flask import Blueprint, render_template, abort, url_for, flash, current_app, redirect, session, request
from datetime import datetime
from ..models.verified_ngos import VerifiedNGO
from ..models.payments import Payment
from ..models.successful_payments import SuccessfulPayment
from ..models.failed_payments import FailedPayment
from ..services.forms import DonationForm
from ..services.email import send_email
from backend import db

donations = Blueprint('donations', __name__)


def finalize_payment(session_id, is_success):
    # NOTE: stripe.api_key should ideally be set once in the app config
    # but setting it here for safety in case it was missed elsewhere.
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    payment = None

    try:
        session_stripe = stripe.checkout.Session.retrieve(session_id)

        payment = Payment.query.filter_by(stripe_session_id=session_id).first()

        if not payment:
            current_app.logger.warning(f"Payment record not found for session: {session_id}")
            return None

        if payment.transaction_status in ('SUCCESS', 'FAILED'):
            return payment

        if is_success:
            SuccessfulPayment_record = SuccessfulPayment(
                stripe_charge_id=session_stripe.payment_intent,
                # amount_received=payment.amount, # Removed assuming this field is handled differently
                receipt_url=session_stripe.url,
                payment=payment,
                confirmed_at=datetime.utcnow()
            )
            db.session.add(SuccessfulPayment_record)

            payment.transaction_status = 'SUCCESS'
            payment.type = 'success'

            ngo = VerifiedNGO.query.get(payment.ngo_id)
            if ngo:
                # Use total_donations_cents for precise addition if model supports it
                ngo.total_donations += payment.amount

            db.session.commit()

            ngo_name = ngo.name if ngo else 'NGO Platform'
            send_email(payment.donor_email, 'Your Donation Receipt', 'donation_success', payment=payment,
                       ngo_name=ngo_name)

        else:
            failure_record = FailedPayment(
                error_message="Payment canceled or rejected by gateway.",
                stripe_error_code=session_stripe.payment_intent,  # Using payment intent as failure code if available
                payment=payment,
                failed_at=datetime.utcnow()
            )
            db.session.add(failure_record)

            payment.transaction_status = 'FAILED'
            payment.type = 'failure'
            db.session.commit()

            ngo_name = VerifiedNGO.query.get(payment.ngo_id).name if VerifiedNGO.query.get(
                payment.ngo_id) else 'NGO Platform'
            send_email(payment.donor_email, 'Your Donation Failed', 'donation_failure', payment=payment,
                       ngo_name=ngo_name, reason='Payment was cancelled or declined.')

    # 🔑 FIX 1: Corrected Stripe exception path 🔑
    except stripe.StripeError as e:
        current_app.logger.error(f"Stripe retrieval failed for session {session_id}: {e}")
        # Note: Added a check for AuthenticationError which causes the second exception in the trace
        if isinstance(e, stripe.error.AuthenticationError):
            current_app.logger.error("CRITICAL: Invalid Stripe API Key. Check configuration.")
            # Optionally, you might want to raise a more fatal error here in production.

        if payment and payment.transaction_status != 'SUCCESS':
            db.session.rollback()
        return None
    except Exception as e:
        current_app.logger.error(f"Internal error during payment finalization for session {session_id}: {e}")
        if payment and payment.transaction_status != 'SUCCESS':
            db.session.rollback()
        return None

    return payment


@donations.route('/donate/<int:ngo_id>', methods=['GET', 'POST'])
def donate_ngo(ngo_id):
    ngo = VerifiedNGO.query.get(ngo_id)

    if ngo is None or not ngo.is_active:
        abort(404)

    form = DonationForm(ngo_id=ngo_id)

    if form.validate_on_submit():
        amount_cents = int(form.amount.data * 100)

        session['donation_data'] = {
            'amount_cents': amount_cents,
            'donor_name': form.donor_name.data,
            'donor_email': form.donor_email.data,
            'ngo_id': ngo_id,
            'ngo_name': ngo.name,
        }

        flash(f'Processing donation of ${form.amount.data} to {ngo.name}. Redirecting to secure payment...', 'info')
        return redirect(url_for('donations.create_checkout_session'))

    return render_template(
        'donate.html',
        ngo=ngo,
        form=form,
        stripe_public_key=current_app.config.get('STRIPE_PUBLIC_KEY', 'pk_test_DUMMY_KEY')
    )


@donations.route('/create-checkout-session', methods=['POST', 'GET'])
def create_checkout_session():
    donation_data = session.get('donation_data')
    if not donation_data:
        flash('Donation session expired or invalid. Please try again.', 'danger')
        return redirect(url_for('home.index'))

    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')

    try:
        new_payment = Payment(
            amount=donation_data['amount_cents'] / 100,
            donor_name=donation_data['donor_name'],
            donor_email=donation_data['donor_email'],
            ngo_id=donation_data['ngo_id'],
            transaction_status='PENDING_INITIATION',
            type='payment'
        )
        db.session.add(new_payment)
        db.session.flush()
        payment_id = new_payment.id

        session_stripe = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': donation_data['amount_cents'],
                    'product_data': {
                        'name': f"Donation to {donation_data['ngo_name']}",
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('donations.payment_success', _external=True) + f'?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=url_for('donations.payment_failed', _external=True) + f'?session_id={{CHECKOUT_SESSION_ID}}',
            metadata={
                'payment_id': payment_id,
                'ngo_id': donation_data['ngo_id']
            },
        )

        new_payment.stripe_session_id = session_stripe.id
        new_payment.transaction_status = 'PENDING'
        db.session.commit()

        session.pop('donation_data', None)

        return redirect(session_stripe.url, code=303)

    # 🔑 FIX 2: Corrected Stripe exception path 🔑
    except stripe.StripeError as e:
        db.session.rollback()
        current_app.logger.error(f"Stripe Session Creation Failed: {e}")
        # Log critical API key failure again for clarity
        if isinstance(e, stripe.error.AuthenticationError):
            current_app.logger.error("CRITICAL: Invalid Stripe API Key error occurred.")

        flash('Payment gateway error. Please try again.', 'danger')
        return redirect(url_for('donations.donate_ngo', ngo_id=donation_data['ngo_id']))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Internal error during checkout session: {e}")
        flash('An internal error occurred. Please try again.', 'danger')
        return redirect(url_for('home.index'))


@donations.route('/payment_success')
def payment_success():
    stripe_session_id = request.args.get('session_id')

    if not stripe_session_id:
        flash('Payment status is ambiguous. Please contact support.', 'warning')
        return redirect(url_for('home.index'))

    payment = finalize_payment(stripe_session_id, is_success=True)

    if payment and payment.transaction_status == 'SUCCESS':
        ngo = VerifiedNGO.query.get(payment.ngo_id)
        return render_template('payment_success.html', payment=payment, ngo=ngo)
    else:
        flash('Payment confirmation failed. Your donation status is pending. Please check your email.', 'danger')
        return redirect(url_for('home.index'))


@donations.route('/payment_failed')
def payment_failed():
    stripe_session_id = request.args.get('session_id')

    if not stripe_session_id:
        flash('Payment status is ambiguous. Please contact support.', 'warning')
        return redirect(url_for('home.index'))

    payment = finalize_payment(stripe_session_id, is_success=False)

    flash('Your payment could not be processed. Please check your card details and try again.', 'danger')
    return render_template('payment_failed.html', payment=payment)