from backend import db
from datetime import datetime

class TempNGO(db.Model):
    __tablename__ = 'temp_ngos'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(128), nullable=False)
    ngo_type = db.Column(db.String(64), nullable=False)
    mission = db.Column(db.Text, nullable=False)
    website = db.Column(db.String(256))

    # FIX: Removed unique=True to allow duplicate email submissions, resolving the IntegrityError.
    contact_email = db.Column(db.String(120), index=True, nullable=False)

    reg_document_path = db.Column(db.String(256), nullable=False)
    financial_report_path = db.Column(db.String(256))

    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"TempNGO(Name: {self.name}, Status: PENDING)"