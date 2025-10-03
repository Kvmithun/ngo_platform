from datetime import datetime
from backend import db

class RejectedNGO(db.Model):
    __tablename__ = 'rejected_ngos'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(128), nullable=False)
    ngo_type = db.Column(db.String(64), nullable=False)
    mission = db.Column(db.Text, nullable=False)
    contact_email = db.Column(db.String(120), index=True, nullable=False)

    reg_document_path = db.Column(db.String(256), nullable=False)
    financial_report_path = db.Column(db.String(256))

    date_rejected = db.Column(db.DateTime, default=datetime.utcnow)
    rejected_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rejection_reason = db.Column(db.Text)

    def __repr__(self):
        return f"RejectedNGO(Name: {self.name}, Rejected: {self.date_rejected.strftime('%Y-%m-%d')})"