from datetime import datetime
from .payments import Payment
from backend import db

class SuccessfulPayment(Payment):
    __tablename__ = 'successful_payments'

    id = db.Column(db.Integer, db.ForeignKey('payments.id'), primary_key=True)

    stripe_charge_id = db.Column(db.String(255), unique=True, nullable=False)
    receipt_url = db.Column(db.String(500), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'success',
    }

    def __repr__(self):
        return f"SuccessfulPayment(ID: {self.id}, Amount: ${self.amount:.2f}, Charge: {self.stripe_charge_id})"