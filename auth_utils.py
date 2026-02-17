# FarmIntel - Auth helpers (password hashing, login required)
import re
from functools import wraps
from flask import session, redirect, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password, method='pbkdf2:sha256')

def check_password(password_hash, password):
    return check_password_hash(password_hash, password)

def farmer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in') or session.get('role') != 'farmer':
            return redirect(url_for('auth.farmer_login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in') or session.get('role') != 'admin':
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated

def login_user(role, user_id, name, email):
    session['logged_in'] = True
    session['role'] = role
    session['user_id'] = user_id
    session['name'] = name
    session['email'] = email

def logout_user():
    session.clear()

def normalize_farmer_login_id(identifier):
    """Accept Farmer ID, email, or mobile."""
    identifier = (identifier or '').strip()
    if not identifier:
        return None
    if re.match(r'^[\d]+$', identifier):
        return ('mobile', identifier)
    if '@' in identifier:
        return ('email', identifier)
    return ('id', identifier)
