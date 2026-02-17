# Crops: farmer view + admin CRUD (API-style for admin, pages for farmer)
import json
import os
from pathlib import Path
from flask import Blueprint, request, redirect, url_for, render_template, flash, session
from db import mysql
from config import Config
from auth_utils import farmer_required, admin_required
from validators import validate_crop_name, validate_positive_number

crops_bp = Blueprint('crops', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def _first_image(image_paths):
    if not image_paths:
        return None
    try:
        arr = json.loads(image_paths) if isinstance(image_paths, str) else image_paths
        return arr[0] if arr else None
    except Exception:
        return image_paths if isinstance(image_paths, str) else None

# ---------- Farmer: list crops ----------
@crops_bp.route('/')
@farmer_required
def list_crops():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM crops WHERE active = 1 ORDER BY name')
    crops = cur.fetchall()
    for c in crops:
        c['first_image'] = _first_image(c.get('image_paths'))
    cur.close()
    return render_template('farmer/crops_list.html', crops=crops)

# ---------- Farmer: crop detail ----------
@crops_bp.route('/<int:crop_id>')
@farmer_required
def crop_detail(crop_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM crops WHERE id = %s AND active = 1', (crop_id,))
    crop = cur.fetchone()
    cur.close()
    if not crop:
        flash('Crop not found.', 'danger')
        return redirect(url_for('crops.list_crops'))
    # Parse image_paths JSON
    images = []
    if crop.get('image_paths'):
        try:
            images = json.loads(crop['image_paths']) if isinstance(crop['image_paths'], str) else crop['image_paths']
        except Exception:
            images = [crop['image_paths']] if crop['image_paths'] else []
    return render_template('farmer/crop_detail.html', crop=crop, images=images)

# ---------- Admin: list all crops ----------
@crops_bp.route('/admin')
@admin_required
def admin_list():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM crops ORDER BY name')
    crops = cur.fetchall()
    for c in crops:
        c['first_image'] = _first_image(c.get('image_paths'))
    cur.close()
    return render_template('admin/crops_list.html', crops=crops)

# ---------- Admin: add crop ----------
@crops_bp.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def admin_add():
    if request.method == 'GET':
        return render_template('admin/crop_form.html', crop=None)
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'Vegetables')
    duration = request.form.get('duration', '').strip()
    avg_price = request.form.get('average_price') or None
    market_price = request.form.get('market_price') or None
    pesticides = request.form.get('pesticides_name', '').strip()
    seeds = request.form.get('best_seeds_name', '').strip()
    fertilizer = request.form.get('fertilizer_name', '').strip()
    season = request.form.get('season', 'Rabi')
    soil_type = request.form.get('soil_type', '').strip()
    demand = request.form.get('india_demand') or None
    description = request.form.get('description', '').strip()
    ok, err = validate_crop_name(name)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('crops.admin_add'))
    if avg_price is not None and str(avg_price).strip():
        ok, err = validate_positive_number(avg_price, 'Average price', required=False)
        if not ok:
            flash(err, 'danger')
            return redirect(url_for('crops.admin_add'))
    if market_price is not None and str(market_price).strip():
        ok, err = validate_positive_number(market_price, 'Market price', required=False)
        if not ok:
            flash(err, 'danger')
            return redirect(url_for('crops.admin_add'))
    image_paths = []
    files = request.files.getlist('crop_images')
    for f in files:
        if f and f.filename and allowed_file(f.filename):
            fn = f"{len(image_paths)}_{f.filename}"
            path = Config.CROP_IMAGES_FOLDER / fn
            f.save(str(path))
            image_paths.append(f'uploads/crops/{fn}')
    cur = mysql.connection.cursor()
    cur.execute('''INSERT INTO crops (name, category, image_paths, duration, average_price, market_price, pesticides_name, best_seeds_name, fertilizer_name, season, soil_type, india_demand, description, active)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)''',
                (name, category, json.dumps(image_paths) if image_paths else None, duration or None, avg_price, market_price, pesticides or None, seeds or None, fertilizer or None, season, soil_type or None, demand, description or None))
    mysql.connection.commit()
    cur.close()
    flash('Crop added successfully.', 'success')
    return redirect(url_for('crops.admin_list'))

# ---------- Admin: edit crop ----------
@crops_bp.route('/admin/edit/<int:crop_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit(crop_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM crops WHERE id = %s', (crop_id,))
    crop = cur.fetchone()
    if not crop:
        cur.close()
        flash('Crop not found.', 'danger')
        return redirect(url_for('crops.admin_list'))
    if request.method == 'GET':
        cur.close()
        images = []
        if crop.get('image_paths'):
            try:
                images = json.loads(crop['image_paths']) if isinstance(crop['image_paths'], str) else crop['image_paths']
            except Exception:
                images = [crop['image_paths']] if crop['image_paths'] else []
        return render_template('admin/crop_form.html', crop=crop, images=images)
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'Vegetables')
    duration = request.form.get('duration', '').strip()
    avg_price = request.form.get('average_price') or None
    market_price = request.form.get('market_price') or None
    pesticides = request.form.get('pesticides_name', '').strip()
    seeds = request.form.get('best_seeds_name', '').strip()
    fertilizer = request.form.get('fertilizer_name', '').strip()
    season = request.form.get('season', 'Rabi')
    soil_type = request.form.get('soil_type', '').strip()
    demand = request.form.get('india_demand') or None
    description = request.form.get('description', '').strip()
    ok, err = validate_crop_name(name)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('crops.admin_edit', crop_id=crop_id))
    if avg_price is not None and str(avg_price).strip():
        ok, err = validate_positive_number(avg_price, 'Average price', required=False)
        if not ok:
            flash(err, 'danger')
            return redirect(url_for('crops.admin_edit', crop_id=crop_id))
    if market_price is not None and str(market_price).strip():
        ok, err = validate_positive_number(market_price, 'Market price', required=False)
        if not ok:
            flash(err, 'danger')
            return redirect(url_for('crops.admin_edit', crop_id=crop_id))
    image_paths = []
    if crop.get('image_paths'):
        try:
            image_paths = json.loads(crop['image_paths']) if isinstance(crop['image_paths'], str) else crop['image_paths'] or []
        except Exception:
            image_paths = [crop['image_paths']] if crop['image_paths'] else []
    files = request.files.getlist('crop_images')
    for f in files:
        if f and f.filename and allowed_file(f.filename):
            fn = f"{len(image_paths)}_{f.filename}"
            path = Config.CROP_IMAGES_FOLDER / fn
            f.save(str(path))
            image_paths.append(f'uploads/crops/{fn}')
    cur.execute('''UPDATE crops SET name=%s, category=%s, image_paths=%s, duration=%s, average_price=%s, market_price=%s, pesticides_name=%s, best_seeds_name=%s, fertilizer_name=%s, season=%s, soil_type=%s, india_demand=%s, description=%s
                   WHERE id=%s''',
                (name, category, json.dumps(image_paths) if image_paths else None, duration or None, avg_price, market_price, pesticides or None, seeds or None, fertilizer or None, season, soil_type or None, demand, description or None, crop_id))
    mysql.connection.commit()
    cur.close()
    flash('Crop updated.', 'success')
    return redirect(url_for('crops.admin_list'))

# ---------- Admin: delete crop ----------
@crops_bp.route('/admin/delete/<int:crop_id>', methods=['POST'])
@admin_required
def admin_delete(crop_id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM crops WHERE id = %s', (crop_id,))
    mysql.connection.commit()
    cur.close()
    flash('Crop deleted.', 'success')
    return redirect(url_for('crops.admin_list'))

# ---------- Admin: toggle active ----------
@crops_bp.route('/admin/toggle/<int:crop_id>', methods=['POST'])
@admin_required
def admin_toggle(crop_id):
    cur = mysql.connection.cursor()
    cur.execute('UPDATE crops SET active = NOT active WHERE id = %s', (crop_id,))
    mysql.connection.commit()
    cur.close()
    flash('Crop status updated.', 'success')
    return redirect(url_for('crops.admin_list'))
