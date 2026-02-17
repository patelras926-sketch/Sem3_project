# Admin panel: login/signup pages (GET), dashboard
from flask import Blueprint, render_template, redirect, url_for
from auth_utils import admin_required

admin_bp = Blueprint('admin_routes', __name__)

@admin_bp.route('/login')
def admin_login_page():
    return render_template('admin/login.html')

@admin_bp.route('/signup')
def admin_signup_page():
    return render_template('admin/signup.html')

@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')
