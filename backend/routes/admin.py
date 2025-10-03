from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse as url_parse
from ..services.forms import AdminLoginForm
from ..models.users import User
from ..models.temp_ngos import TempNGO
from ..models.verified_ngos import VerifiedNGO
from ..models.rejected_ngos import RejectedNGO
from backend import db

admin = Blueprint('admin', __name__)


@admin.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    form = AdminLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(form.password.data) or not user.is_admin():
            flash('Invalid admin credentials.', 'danger')
            return redirect(url_for('admin.login'))

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('admin.dashboard')

        return redirect(next_page)

    # FIX: Pass 'now' object for the base.html footer
    return render_template('admin_login.html', form=form, now=datetime.now())


@admin.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home.index'))


@admin.route('/')
@login_required
def dashboard():
    if not current_user.is_admin():
        flash('Access denied: You do not have administrator privileges.', 'danger')
        logout_user()
        return redirect(url_for('home.index'))

    return redirect(url_for('admin.list_pending_ngos'))


@admin.route('/pending')
@login_required
def list_pending_ngos():
    if not current_user.is_admin():
        flash('Access denied: Administrator privileges required.', 'danger')
        return redirect(url_for('home.index'))

    pending_ngos = TempNGO.query.order_by(TempNGO.date_submitted.asc()).all()

    return render_template(
        'admin/pending_ngos.html',
        ngos=pending_ngos,
        page_title='Pending Applications',
        endpoint='admin.list_pending_ngos',
        now=datetime.now()  # Added 'now' for consistency
    )


@admin.route('/approve/<int:ngo_id>', methods=['POST'])
@login_required
def approve_ngo(ngo_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('home.index'))

    temp_ngo = TempNGO.query.get_or_404(ngo_id)

    try:
        # 🔥 FINAL FIX: Only include fields that EXIST in the VerifiedNGO model.
        # Removed 'approved_by_admin_id' and fields not in TempNGO (contact_phone, location).
        verified_ngo = VerifiedNGO(
            name=temp_ngo.name,
            ngo_type=temp_ngo.ngo_type,
            mission=temp_ngo.mission,
            contact_email=temp_ngo.contact_email,

            # Nullable fields from VerifiedNGO set to None (or defaulted)
            contact_phone=None,
            location=None
            # date_approved uses the default=datetime.utcnow set in the model
        )

        db.session.add(verified_ngo)
        db.session.delete(temp_ngo)
        db.session.commit()

        flash(f'Successfully approved and verified: {temp_ngo.name}', 'success')

    except Exception as e:
        db.session.rollback()

        current_app.logger.error(f"Integrity Error during NGO Approval {ngo_id}: {e}")

        error_message = str(e)
        if "UNIQUE constraint failed" in error_message:
            # This will catch if the Name or Email is submitted twice to the Verified table
            flash(
                'Approval failed: An organization with this Name or Email already exists in the Verified list. Check model constraints.',
                'danger')
        else:
            # This will catch the final, fatal error (like the missing column)
            flash('Approval failed due to a critical database error. See console for details.', 'danger')

    return redirect(url_for('admin.list_pending_ngos'))

@admin.route('/reject/<int:ngo_id>', methods=['POST'])
@login_required
def reject_ngo(ngo_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('home.index'))

    temp_ngo = TempNGO.query.get_or_404(ngo_id)

    try:
        rejected_ngo = RejectedNGO(
            name=temp_ngo.name,
            ngo_type=temp_ngo.ngo_type,
            mission=temp_ngo.mission,
            contact_email=temp_ngo.contact_email,
            reg_document_path=temp_ngo.reg_document_path,
            financial_report_path=temp_ngo.financial_report_path,
            rejected_by_admin_id=current_user.id,
            rejection_reason="Manual rejection by admin."
        )

        db.session.add(rejected_ngo)
        db.session.delete(temp_ngo)
        db.session.commit()

        flash(f'Successfully rejected and archived: {temp_ngo.name}.', 'info')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting NGO {ngo_id}: {e}")
        flash('Rejection failed due to a database error.', 'danger')

    return redirect(url_for('admin.list_pending_ngos'))


@admin.route('/verified')
@login_required
def list_verified_ngos():
    if not current_user.is_admin():
        flash('Access denied: Administrator privileges required.', 'danger')
        return redirect(url_for('home.index'))

    verified_ngos = VerifiedNGO.query.order_by(VerifiedNGO.date_approved.desc()).all()

    return render_template(
        'admin/verified_ngos.html',
        ngos=verified_ngos,
        page_title='Verified Organizations',
        endpoint='admin.list_verified_ngos',
        now=datetime.utcnow()
    )


@admin.route('/manage_verified/<int:ngo_id>')
@login_required
def manage_verified_ngo(ngo_id):
    return f"Management page for Verified NGO ID: {ngo_id}"


@admin.route('/rejected')
@login_required
def list_rejected_ngos():
    if not current_user.is_admin():
        flash('Access denied: Administrator privileges required.', 'danger')
        return redirect(url_for('home.index'))

    rejected_ngos = RejectedNGO.query.order_by(RejectedNGO.date_rejected.desc()).all()

    return render_template(
        'admin/rejected_ngos.html',
        ngos=rejected_ngos,
        page_title='Rejected Applications',
        endpoint='admin.list_rejected_ngos',
        now=datetime.utcnow()
    )


@admin.route('/restore/<int:ngo_id>', methods=['POST'])
@login_required
def restore_ngo(ngo_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('home.index'))

    rejected_ngo = RejectedNGO.query.get_or_404(ngo_id)

    try:
        temp_ngo = TempNGO(
            name=rejected_ngo.name,
            ngo_type=rejected_ngo.ngo_type,
            mission=rejected_ngo.mission,
            contact_email=rejected_ngo.contact_email,
            reg_document_path=rejected_ngo.reg_document_path,
            financial_report_path=rejected_ngo.financial_report_path,
            date_submitted=datetime.utcnow()
        )

        db.session.add(temp_ngo)
        db.session.delete(rejected_ngo)
        db.session.commit()

        flash(f'Successfully restored {rejected_ngo.name} to the Pending Applications queue.', 'info')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error restoring NGO {ngo_id}: {e}")
        flash('Restoration failed due to a database error.', 'danger')

    return redirect(url_for('admin.list_rejected_ngos'))