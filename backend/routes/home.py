# backend/routes/home.py

from flask import Blueprint, render_template
from ..models.verified_ngos import VerifiedNGO
from datetime import datetime # ADD THIS IMPORT

home = Blueprint('home', __name__)

@home.route('/')
def index():
    try:
        verified_ngos = VerifiedNGO.query.filter_by(is_active=True).order_by(
            VerifiedNGO.total_donations.desc()
        ).all()

        # FIX 1: Pass 'now' object for successful rendering
        return render_template('home.html', title='Home', ngos=verified_ngos, now=datetime.now())

    except Exception as e:
        print(f"Database query error on home page: {e}")
        # FIX 2: Also pass 'now' object when rendering the error state
        return render_template('home.html', title='Home', ngos=[], error="Failed to load NGOs.", now=datetime.now())