# Farmer & Admin Login/Signup - no prefix; routes define full path
from flask import Blueprint, request, redirect, url_for, render_template, session, flash
from db import mysql
from auth_utils import hash_password, check_password, login_user, logout_user, normalize_farmer_login_id
from validators import (
    validate_email,
    validate_mobile,
    validate_name,
    validate_password,
    validate_confirm_password,
    validate_land_area,
    validate_identifier,
    normalize_mobile,
)

auth_bp = Blueprint('auth', __name__)

# ---------- Farmer Login ----------
@auth_bp.route('/farmer/login', methods=['GET', 'POST'])
def farmer_login():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        ok, err = validate_identifier(identifier, 'Farmer ID, Email or Mobile')
        if not ok:
            flash(err, 'danger')
            return redirect(url_for('auth.farmer_login'))
        if not password:
            flash('Password is required.', 'danger')
            return redirect(url_for('auth.farmer_login'))
        key, value = normalize_farmer_login_id(identifier)
        cur = mysql.connection.cursor()
        if key == 'email':
            cur.execute('SELECT id, role, name, email, password_hash FROM users WHERE role = %s AND email = %s', ('farmer', value))
        elif key == 'mobile':
            cur.execute('SELECT id, role, name, email, password_hash FROM users WHERE role = %s AND mobile = %s', ('farmer', value))
        else:
            cur.execute('SELECT id, role, name, email, password_hash FROM users WHERE role = %s AND id = %s', ('farmer', value))
        user = cur.fetchone()
        cur.close()
        if user and check_password(user['password_hash'], password):
            login_user('farmer', user['id'], user['name'], user['email'])
            return redirect(url_for('farmer.dashboard'))
        flash('Invalid Farmer ID/Email/Mobile or Password.', 'danger')
    return render_template('farmer/login.html')

# ---------- Farmer Signup ----------
@auth_bp.route('/farmer/signup', methods=['POST'])
def farmer_signup():
    name = request.form.get('name', '').strip()
    mobile = request.form.get('mobile', '').strip()
    email = request.form.get('email', '').strip()
    village = request.form.get('village', '').strip()
    taluka = request.form.get('taluka', '').strip()
    district = request.form.get('district', '').strip()
    land_area = request.form.get('land_area') or None
    soil_type = request.form.get('soil_type', '').strip()
    water_availability = request.form.get('water_availability', '').strip()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')
    # Validation
    ok, err = validate_name(name, 'Farmer full name')
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('farmer.signup_page'))
    ok, err = validate_mobile(mobile, required=True)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('farmer.signup_page'))
    ok, err = validate_email(email)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('farmer.signup_page'))
    ok, err = validate_password(password)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('farmer.signup_page'))
    ok, err = validate_confirm_password(password, confirm)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('farmer.signup_page'))
    if land_area is not None and str(land_area).strip():
        ok, err = validate_land_area(land_area, required=False)
        if not ok:
            flash(err, 'danger')
            return redirect(url_for('farmer.signup_page'))
    cur = mysql.connection.cursor()
    cur.execute('SELECT id FROM users WHERE email = %s', (email,))
    if cur.fetchone():
        cur.close()
        flash('Email already registered.', 'danger')
        return redirect(url_for('farmer.signup_page'))
    mobile_clean = normalize_mobile(mobile) or mobile
    cur.execute('''INSERT INTO users (role, name, email, mobile, password_hash, village, taluka, district, land_area, soil_type, water_availability)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                ('farmer', name, email, mobile_clean, hash_password(password), village or None, taluka or None, district or None, land_area, soil_type or None, water_availability or None))
    mysql.connection.commit()
    cur.close()
    flash('Registration successful. Please login.', 'success')
    return redirect(url_for('auth.farmer_login'))

# ---------- Admin Login ----------
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        ok, err = validate_identifier(identifier, 'Admin Username or Email')
        if not ok:
            flash(err, 'danger')
            return redirect(url_for('auth.admin_login'))
        if not password:
            flash('Password is required.', 'danger')
            return redirect(url_for('auth.admin_login'))
        cur = mysql.connection.cursor()
        cur.execute('SELECT id, role, name, email, password_hash FROM users WHERE role = %s AND (email = %s OR name = %s)', ('admin', identifier, identifier))
        user = cur.fetchone()
        cur.close()
        if user and check_password(user['password_hash'], password):
            login_user('admin', user['id'], user['name'], user['email'])
            return redirect(url_for('admin_routes.admin_dashboard'))
        flash('Invalid Admin credentials.', 'danger')
    return render_template('admin/login.html')

# ---------- Admin Signup ----------
@auth_bp.route('/admin/signup', methods=['POST'])
def admin_signup():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    mobile = request.form.get('mobile', '').strip()
    admin_role = request.form.get('admin_role', '').strip()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')
    # Validation
    ok, err = validate_name(name, 'Admin name')
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('admin_routes.admin_signup_page'))
    ok, err = validate_email(email)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('admin_routes.admin_signup_page'))
    if mobile:
        ok, err = validate_mobile(mobile, required=False)
        if not ok:
            flash(err, 'danger')
            return redirect(url_for('admin_routes.admin_signup_page'))
    ok, err = validate_password(password)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('admin_routes.admin_signup_page'))
    ok, err = validate_confirm_password(password, confirm)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('admin_routes.admin_signup_page'))
    cur = mysql.connection.cursor()
    cur.execute('SELECT id FROM users WHERE email = %s', (email,))
    if cur.fetchone():
        cur.close()
        flash('Email already registered.', 'danger')
        return redirect(url_for('admin_routes.admin_signup_page'))
    mobile_clean = normalize_mobile(mobile) if mobile else ''
    cur.execute('''INSERT INTO users (role, name, email, mobile, password_hash, admin_role)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                ('admin', name, email, mobile_clean, hash_password(password), admin_role or None))
    mysql.connection.commit()
    cur.close()
    flash('Admin account created. Please login.', 'success')
    return redirect(url_for('auth.admin_login'))

# ---------- Logout (both) ----------
@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.farmer_login'))
