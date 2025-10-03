from datetime import datetime
from backend import db

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)

    donor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ngo_id = db.Column(db.Integer, db.ForeignKey('verified_ngos.id'), nullable=False)

    donor_name = db.Column(db.String(100), nullable=True)
    donor_email = db.Column(db.String(120), nullable=False)

    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)

    stripe_session_id = db.Column(db.String(255), unique=True, nullable=True)
    transaction_status = db.Column(db.String(50), default='PENDING', nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    type = db.Column(db.String(50), nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'payment',
        'polymorphic_on': type
    }

    def __repr__(self):
        status = self.transaction_status
        return f"Payment(ID: {self.id}, NGO: {self.ngo_id}, Amount: ${self.amount:.2f}, Status: {status})"