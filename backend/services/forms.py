from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField, PasswordField, BooleanField, DecimalField, \
    HiddenField
from wtforms.validators import DataRequired, Email, Length, URL, Optional, NumberRange, InputRequired

NGO_TYPES = [
    ('Education', 'Education'),
    ('Health', 'Health & Wellness'),
    ('Environment', 'Environmental Conservation'),
    ('Poverty', 'Poverty Alleviation'),
    ('Arts', 'Arts & Culture'),
    ('Animal Welfare', 'Animal Welfare'),
    ('Other', 'Other (Please specify in mission)')
]


class EmailForm(FlaskForm):
    email = StringField('NGO Contact Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    submit = SubmitField('Send Registration Link')


class NGOForm(FlaskForm):
    # ✅ FIX: Restored to original field types but keeping validators set to Optional()
    name = StringField('Official NGO Name', validators=[Optional(), Length(max=128)])

    # ✅ FIX: Restored to original field types but keeping validators set to Optional()
    ngo_type = SelectField('Primary Focus Area', choices=NGO_TYPES, validators=[Optional()])

    mission = TextAreaField('Mission Statement & Summary of Activities', validators=[
        Optional(),
        Length(min=50, max=1000)
    ])

    # Final fix (No validators) remains here
    contact_email = StringField('Contact Email', validators=[], render_kw={'readonly': True})

    # Final fix (Removed URL validator) remains here
    website = StringField('Official Website (Optional)', validators=[Optional()])

    registration_document = FileField('Legal Registration Document (e.g., 501(c)3, Charity Commission)', validators=[
        Optional(),
        FileAllowed(['pdf', 'jpg', 'png'])
    ])

    financial_report = FileField('Latest Annual Financial Report (Optional)', validators=[
        Optional(),
        FileAllowed(['pdf'])
    ])

    submit = SubmitField('Submit Application for Review')


class AdminLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class SearchForm(FlaskForm):
    search_term = StringField('Keyword Search', validators=[Length(max=100)])
    category = SelectField('Category', choices=[('', 'All Categories')] + NGO_TYPES, validators=[Optional()])
    location = StringField('Location/City', validators=[Length(max=50)])
    submit = SubmitField('Search')


class DonationForm(FlaskForm):
    donor_name = StringField('Your Name (Optional)', validators=[Length(max=100), Optional()])

    donor_email = StringField('Your Email', validators=[
        InputRequired(),
        Email(),
        Length(max=120)
    ])

    amount = DecimalField('Donation Amount ($)', validators=[
        InputRequired(),
        NumberRange(min=1.00)
    ], places=2, render_kw={'step': '0.01'})

    ngo_id = HiddenField(validators=[InputRequired()])

    submit = SubmitField('Proceed to Payment')