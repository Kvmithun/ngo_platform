import os
# 🔥 FIX: Added 'request' and 'CombinedMultiDict' to imports
from flask import Blueprint, render_template, flash, redirect, url_for, current_app, request
from werkzeug.datastructures import CombinedMultiDict  # <-- NEEDED FOR FILE UPLOAD FIX
from ..services.forms import EmailForm, NGOForm
from ..services.utils import generate_registration_token, confirm_registration_token, save_document
from ..services.email import send_email
from ..models.temp_ngos import TempNGO
from backend import db
from datetime import datetime

registration = Blueprint('registration', __name__)


@registration.route('/register', methods=['GET', 'POST'])
def register():
    form = EmailForm()

    if form.validate_on_submit():
        ngo_email = form.email.data

        if TempNGO.query.filter_by(contact_email=ngo_email).first():
            flash('An application with this email address is already pending review.', 'warning')
            return redirect(url_for('registration.confirmation'))

        token = generate_registration_token(ngo_email)
        registration_url = url_for('registration.ngo_form', token=token, _external=True)

        try:
            send_email(
                to=ngo_email,
                subject='Complete Your NGO Registration',
                template='reg_link',
                url=registration_url
            )
            flash(f'A secure registration link has been sent to {ngo_email}. Please check your inbox.', 'success')
        except Exception as e:
            current_app.logger.error(f"Failed to send registration email to {ngo_email}: {e}")
            flash('Error: Could not send the registration link. Please check email configuration or try again later.',
                  'danger')

        return redirect(url_for('registration.register'))

    return render_template('register.html', form=form, now=datetime.now())


@registration.route('/ngo-form/<token>', methods=['GET', 'POST'])
def ngo_form(token):
    email = confirm_registration_token(token)

    if not email:
        flash('The registration link is invalid or has expired. Please re-enter your email to receive a new link.',
              'danger')
        return redirect(url_for('registration.register'))

    if TempNGO.query.filter_by(contact_email=email).first():
        flash('An application with this email address is already pending review.', 'warning')
        return redirect(url_for('registration.confirmation'))

    if request.method == 'POST':
        # 🔥 FINAL REGRESSION FIX: Explicitly combine form text data AND file data
        # This restores FileField functionality that was lost in complex POST requests.
        combined_data = CombinedMultiDict((request.files, request.form))
        form = NGOForm(combined_data, contact_email=email)
    else:
        # On GET, initialize normally, using the email from the token
        form = NGOForm(contact_email=email)

    if form.validate_on_submit():
        try:
            # 1. Handle File Uploads (This block now correctly receives the file data)
            reg_doc_path = None
            if form.registration_document.data and form.registration_document.data.filename:
                reg_doc_path = save_document(form.registration_document.data)

            # 2. Handle Optional File Upload
            financial_doc_path = None
            if form.financial_report.data and form.financial_report.data.filename:
                financial_doc_path = save_document(form.financial_report.data)

            # Use placeholder if the file was submitted as optional (or failed to save)
            final_reg_doc_path = reg_doc_path if reg_doc_path else "N/A (File Optional)"

            # FINAL DATA FIX: Intercept empty strings from optional fields and convert to None
            submitted_website = form.website.data
            final_website = submitted_website if submitted_website else None

            new_ngo = TempNGO(
                name=form.name.data,
                ngo_type=form.ngo_type.data,
                mission=form.mission.data,
                website=final_website,  # Use the corrected data (None if empty)
                contact_email=email,
                reg_document_path=final_reg_doc_path,
                financial_report_path=financial_doc_path
            )

            db.session.add(new_ngo)
            db.session.commit()

            # Note: Add the send_email for admin notification here

            flash('Application submitted successfully! It is now under review.', 'success')
            return redirect(url_for('registration.confirmation'))

        except Exception as e:
            db.session.rollback()
            error_message = str(e)

            # Targeted error handling for database constraint violations
            if "IntegrityError" in error_message or "UNIQUE constraint failed" in error_message:
                flash(
                    'An application with this email already exists in the system. Please use a unique email or contact support.',
                    'danger')
                current_app.logger.warning(f"Integrity Error during NGO submission for {email}: {error_message}")
            else:
                # General error handling - Logs if File Save Failed
                current_app.logger.error(f"Critical Error saving NGO form data for {email}: {error_message}")
                flash('An unexpected error occurred while saving your application. Please try again.', 'danger')

            # Fall through to the final return, which re-renders the form with submitted data
            pass

            # Render the form (it will now be correctly populated with request.form data if POST failed)
    return render_template('ngo_form.html', form=form, token=token, now=datetime.now())


@registration.route('/confirmation')
def confirmation():
    return render_template('confirmation.html', now=datetime.now())
