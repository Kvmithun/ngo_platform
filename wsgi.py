import os
from backend import create_app, db
from backend.models.users import User
from backend.models.verified_ngos import VerifiedNGO

config_name = os.environ.get('FLASK_CONFIG', 'default')
app = create_app(config_name)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, VerifiedNGO=VerifiedNGO)