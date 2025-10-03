from flask import Blueprint, render_template, request, url_for
from sqlalchemy import or_
from ..services.forms import SearchForm
from ..models.verified_ngos import VerifiedNGO
from datetime import datetime

search = Blueprint('search', __name__)

@search.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm(request.form if request.method == 'POST' else None)
    results = []
    query_executed = False

    # Default list
    default_results = VerifiedNGO.query.filter_by(is_active=True).order_by(
        VerifiedNGO.date_approved.desc()
    ).limit(12).all()

    # Run search only on POST
    if request.method == 'POST' and form.validate():
        query_executed = True

        query = VerifiedNGO.query.filter_by(is_active=True)
        filters_applied = False

        # Keyword Search
        search_term = form.search_term.data
        if search_term and search_term.strip():
            search_pattern = f'%{search_term}%'
            query = query.filter(or_(
                VerifiedNGO.name.ilike(search_pattern),
                VerifiedNGO.mission.ilike(search_pattern)
            ))
            filters_applied = True

        # Category Filter
        category = form.category.data
        if category and category.strip() != '' and category != 'All Categories':
            search_pattern = f'%{category}%'
            query = query.filter(VerifiedNGO.ngo_type.ilike(search_pattern))
            filters_applied = True

        results = query.order_by(VerifiedNGO.name).all()

        # If nothing applied → default
        if not filters_applied:
            results = default_results
    else:
        # First load → default
        results = default_results

    return render_template(
        'search.html',
        form=form,
        results=results,
        query_executed=query_executed,
        now=datetime.now()
    )
