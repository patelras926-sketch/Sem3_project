# Government Schemes: admin CRUD, farmer view
from flask import Blueprint, request, redirect, url_for, render_template, flash
from db import mysql
from auth_utils import farmer_required, admin_required
from validators import validate_required_string

schemes_bp = Blueprint('schemes', __name__)

# ---------- Farmer: list schemes ----------
@schemes_bp.route('/')
@farmer_required
def list_schemes():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM schemes WHERE status = %s ORDER BY name', ('Active',))
    schemes = cur.fetchall()
    cur.close()
    return render_template('farmer/schemes_list.html', schemes=schemes)

# ---------- Admin: list all ----------
@schemes_bp.route('/admin')
@admin_required
def admin_list():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM schemes ORDER BY name')
    schemes = cur.fetchall()
    cur.close()
    return render_template('admin/schemes_list.html', schemes=schemes)

# ---------- Admin: add ----------
@schemes_bp.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def admin_add():
    if request.method == 'GET':
        return render_template('admin/scheme_form.html', scheme=None)
    name = request.form.get('name', '').strip()
    scheme_type = request.form.get('scheme_type', 'Central')
    eligible_crop = request.form.get('eligible_crop', '').strip()
    eligibility = request.form.get('eligibility_criteria', '').strip()
    benefits = request.form.get('benefits', '').strip()
    documents = request.form.get('required_documents', '').strip()
    apply_link = request.form.get('apply_link', '').strip()
    status = request.form.get('status', 'Active')
    ok, err = validate_required_string(name, 'Scheme name', max_len=200)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('schemes.admin_add'))
    cur = mysql.connection.cursor()
    cur.execute('''INSERT INTO schemes (name, scheme_type, eligible_crop, eligibility_criteria, benefits, required_documents, apply_link, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                (name, scheme_type, eligible_crop or None, eligibility or None, benefits or None, documents or None, apply_link or None, status))
    mysql.connection.commit()
    cur.close()
    flash('Scheme added.', 'success')
    return redirect(url_for('schemes.admin_list'))

# ---------- Admin: edit ----------
@schemes_bp.route('/admin/edit/<int:scheme_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit(scheme_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM schemes WHERE id = %s', (scheme_id,))
    scheme = cur.fetchone()
    if not scheme:
        cur.close()
        flash('Scheme not found.', 'danger')
        return redirect(url_for('schemes.admin_list'))
    if request.method == 'GET':
        cur.close()
        return render_template('admin/scheme_form.html', scheme=scheme)
    name = request.form.get('name', '').strip()
    scheme_type = request.form.get('scheme_type', 'Central')
    eligible_crop = request.form.get('eligible_crop', '').strip()
    eligibility = request.form.get('eligibility_criteria', '').strip()
    benefits = request.form.get('benefits', '').strip()
    documents = request.form.get('required_documents', '').strip()
    apply_link = request.form.get('apply_link', '').strip()
    status = request.form.get('status', 'Active')
    ok, err = validate_required_string(name, 'Scheme name', max_len=200)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('schemes.admin_edit', scheme_id=scheme_id))
    cur.execute('''UPDATE schemes SET name=%s, scheme_type=%s, eligible_crop=%s, eligibility_criteria=%s, benefits=%s, required_documents=%s, apply_link=%s, status=%s WHERE id=%s''',
                (name, scheme_type, eligible_crop or None, eligibility or None, benefits or None, documents or None, apply_link or None, status, scheme_id))
    mysql.connection.commit()
    cur.close()
    flash('Scheme updated.', 'success')
    return redirect(url_for('schemes.admin_list'))

# ---------- Admin: delete ----------
@schemes_bp.route('/admin/delete/<int:scheme_id>', methods=['POST'])
@admin_required
def admin_delete(scheme_id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM schemes WHERE id = %s', (scheme_id,))
    mysql.connection.commit()
    cur.close()
    flash('Scheme deleted.', 'success')
    return redirect(url_for('schemes.admin_list'))
