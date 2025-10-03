import os
from werkzeug.security import generate_password_hash
from backend import db, create_app
from backend.models.users import User
from backend.models.verified_ngos import VerifiedNGO # Still imported for db.create_all()
from datetime import datetime

config_name = os.environ.get('FLASK_CONFIG', 'development')
app = create_app(config_name)

def seed_database():
    with app.app_context():
        print("Starting database seeding...")

        # Create all tables defined in your models
        db.create_all()

        # Seed Admin User
        admin_email = 'admin@gotham.com'
        if not User.query.filter_by(email=admin_email).first():
            hashed_password = generate_password_hash("batman123")
            admin = User(
                email=admin_email,
                username='admin_wayne',
                password_hash=hashed_password,
                role=1
            )
            db.session.add(admin)
            print(f"Seeded Admin: {admin_email} (Password: batman123)")
        else:
            print(f"Admin user {admin_email} already exists. Skipping.")

        # Removed the code block for seeding Verified NGOs.

        db.session.commit()
        print("Database seeding complete.")

if __name__ == '__main__':
    seed_database()
