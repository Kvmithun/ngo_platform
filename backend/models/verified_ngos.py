from datetime import datetime
from backend import db

class VerifiedNGO(db.Model):
    __tablename__ = 'verified_ngos'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)

    contact_email = db.Column(db.String(120), unique=True, nullable=False)

    ngo_type = db.Column(db.String(50), nullable=False, index=True)
    mission = db.Column(db.Text, nullable=False)
    contact_phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(100), nullable=True, index=True)

    is_active = db.Column(db.Boolean, default=True)
    total_donations = db.Column(db.Float, default=0.00)

    date_approved = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship(
        'Payment',
        backref='receiving_ngo',
        lazy='dynamic',
        foreign_keys='Payment.ngo_id'
    )

    def __repr__(self):
        return f"VerifiedNGO(Name: {self.name}, Type: {self.ngo_type}, Active: {self.is_active})"