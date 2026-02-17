# Farmer panel: login/signup pages (GET), dashboard
from flask import Blueprint, render_template, redirect, url_for
from auth_utils import farmer_required

farmer_bp = Blueprint('farmer', __name__)

@farmer_bp.route('/login')
def login_page():
    return render_template('farmer/login.html')

@farmer_bp.route('/signup')
def signup_page():
    return render_template('farmer/signup.html')

@farmer_bp.route('/dashboard')
@farmer_required
def dashboard():
    return render_template('farmer/dashboard.html')
