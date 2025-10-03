import os
import secrets
import logging
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


def generate_registration_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='ngo-reg-salt')


def confirm_registration_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(
            token,
            salt='ngo-reg-salt',
            max_age=expiration
        )
    except:
        return False
    return email


def save_document(file_data):
    # CRITICAL: Define folder name and path calculation here
    folder_name = 'ngo_documents'

    if not file_data or not getattr(file_data, 'filename', None):
        logger.warning("save_document received no valid file data.")
        return None

    _, f_ext = os.path.splitext(file_data.filename)
    random_hex = secrets.token_hex(8)
    safe_file_name = secure_filename(random_hex + f_ext)

    # Calculate absolute path: ProjectRoot/static/ngo_documents/
    upload_dir = os.path.join(current_app.root_path, 'static', folder_name)

    if not os.path.exists(upload_dir):
        try:
            os.makedirs(upload_dir, mode=0o755)
        except OSError as e:
            logger.error(f"Directory creation failed for {upload_dir}. Error: {e}")
            return None

    file_path = os.path.join(upload_dir, safe_file_name)

    logger.info(f"Attempting to save file: {safe_file_name} to path: {file_path}")

    try:
        file_data.save(file_path)
        logger.info(f"File saved successfully: {safe_file_name}")
    except Exception as e:
        logger.error(f"FILE SAVE FAILED: Could not write file to disk. Error: {e}")
        return None

    # Return the path relative to the static folder for URL generation
    return os.path.join(folder_name, safe_file_name)