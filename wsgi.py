import os
from backend import create_app, db
from backend.models.users import User
from backend.models.verified_ngos import VerifiedNGO

# IMPORT MIGRATION UTILITY
from flask_migrate import upgrade

config_name = os.environ.get('FLASK_CONFIG', 'default')
app = create_app(config_name)

# 🛠️ TEMPORARY FIX: FORCE DATABASE MIGRATION ON STARTUP
with app.app_context():
    try:
        # Run database upgrade to create all missing tables (users, temp_ngos, etc.)
        # This resolves the UndefinedTable error.
        print("INFO: Running database upgrade...")
        upgrade()
        print("INFO: Database tables successfully created/updated.")
    except Exception as e:
        # We print but don't fail the app context if migration fails (e.g., table already exists)
        print(f"WARNING: Database migration failed during startup: {e}")
# -----------------------------------------------------------

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, VerifiedNGO=VerifiedNGO)

# NOTE: Since you are using Gunicorn, this file must return the app instance.
# If this is wsgi.py, Gunicorn finds the 'app' object.