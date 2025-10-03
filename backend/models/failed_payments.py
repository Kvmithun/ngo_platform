from datetime import datetime
from .payments import Payment
from backend import db

class FailedPayment(Payment):
    __tablename__ = 'failed_payments'

    id = db.Column(db.Integer, db.ForeignKey('payments.id'), primary_key=True)

    error_message = db.Column(db.Text, nullable=True)
    stripe_error_code = db.Column(db.String(100), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'failure',
    }

    def __repr__(self):
        return f"FailedPayment(ID: {self.id}, Amount: ${self.amount:.2f}, Error: {self.stripe_error_code})"