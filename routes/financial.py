# Farmer Financial Analysis: expense, income, profit/loss
import csv
import io
from decimal import Decimal
from flask import Blueprint, request, redirect, url_for, render_template, flash, session, Response
from db import mysql
from auth_utils import farmer_required
from validators import validate_crop_name, validate_positive_number

financial_bp = Blueprint('financial', __name__)

def _compute_totals(records):
    for r in records:
        r['total_expense'] = (Decimal(str(r['seeds_cost'] or 0)) + Decimal(str(r['fertilizer_cost'] or 0)) +
                              Decimal(str(r['pesticides_cost'] or 0)) + Decimal(str(r['irrigation_cost'] or 0)) +
                              Decimal(str(r['labour_cost'] or 0)) + Decimal(str(r['machinery_cost'] or 0)) +
                              Decimal(str(r['other_expenses'] or 0)))
        prod = Decimal(str(r['total_production'] or 0))
        price = Decimal(str(r['selling_price'] or 0))
        r['total_income'] = prod * price
        r['net_profit'] = r['total_income'] - r['total_expense']
        if r['net_profit'] > 0:
            r['status'] = 'Profit'
        elif r['net_profit'] < 0:
            r['status'] = 'Loss'
        else:
            r['status'] = 'No Profit No Loss'
    return records

@financial_bp.route('/')
@farmer_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM financial_records WHERE farmer_id = %s ORDER BY created_at DESC', (session['user_id'],))
    records = cur.fetchall()
    cur.close()
    _compute_totals(records)
    return render_template('farmer/financial_dashboard.html', records=records)

@financial_bp.route('/add', methods=['GET', 'POST'])
@farmer_required
def add_record():
    if request.method == 'GET':
        return render_template('farmer/financial_form.html', record=None)
    crop_name = request.form.get('crop_name', '').strip()
    season = request.form.get('season', '').strip()
    seeds = request.form.get('seeds_cost') or 0
    fertilizer = request.form.get('fertilizer_cost') or 0
    pesticides = request.form.get('pesticides_cost') or 0
    irrigation = request.form.get('irrigation_cost') or 0
    labour = request.form.get('labour_cost') or 0
    machinery = request.form.get('machinery_cost') or 0
    other = request.form.get('other_expenses') or 0
    production = request.form.get('total_production') or 0
    selling_price = request.form.get('selling_price') or 0
    ok, err = validate_crop_name(crop_name)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('financial.add_record'))
    for val, label in [
        (seeds, 'Seeds cost'), (fertilizer, 'Fertilizer cost'), (pesticides, 'Pesticides cost'),
        (irrigation, 'Irrigation cost'), (labour, 'Labour cost'), (machinery, 'Machinery cost'),
        (other, 'Other expenses'), (production, 'Total production'), (selling_price, 'Selling price')
    ]:
        ok, err = validate_positive_number(val, label, required=False)
        if not ok:
            flash(err, 'danger')
            return redirect(url_for('financial.add_record'))
    cur = mysql.connection.cursor()
    cur.execute('''INSERT INTO financial_records (farmer_id, crop_name, season, seeds_cost, fertilizer_cost, pesticides_cost, irrigation_cost, labour_cost, machinery_cost, other_expenses, total_production, selling_price)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (session['user_id'], crop_name, season or None, seeds, fertilizer, pesticides, irrigation, labour, machinery, other, production, selling_price))
    mysql.connection.commit()
    cur.close()
    flash('Record added. View in dashboard.', 'success')
    return redirect(url_for('financial.dashboard'))

@financial_bp.route('/edit/<int:record_id>', methods=['GET', 'POST'])
@farmer_required
def edit_record(record_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM financial_records WHERE id = %s AND farmer_id = %s', (record_id, session['user_id']))
    record = cur.fetchone()
    if not record:
        cur.close()
        flash('Record not found.', 'danger')
        return redirect(url_for('financial.dashboard'))
    if request.method == 'GET':
        cur.close()
        return render_template('farmer/financial_form.html', record=record)
    crop_name = request.form.get('crop_name', '').strip()
    season = request.form.get('season', '').strip()
    seeds = request.form.get('seeds_cost') or 0
    fertilizer = request.form.get('fertilizer_cost') or 0
    pesticides = request.form.get('pesticides_cost') or 0
    irrigation = request.form.get('irrigation_cost') or 0
    labour = request.form.get('labour_cost') or 0
    machinery = request.form.get('machinery_cost') or 0
    other = request.form.get('other_expenses') or 0
    production = request.form.get('total_production') or 0
    selling_price = request.form.get('selling_price') or 0
    ok, err = validate_crop_name(crop_name)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('financial.edit_record', record_id=record_id))
    for val, label in [
        (seeds, 'Seeds cost'), (fertilizer, 'Fertilizer cost'), (pesticides, 'Pesticides cost'),
        (irrigation, 'Irrigation cost'), (labour, 'Labour cost'), (machinery, 'Machinery cost'),
        (other, 'Other expenses'), (production, 'Total production'), (selling_price, 'Selling price')
    ]:
        ok, err = validate_positive_number(val, label, required=False)
        if not ok:
            flash(err, 'danger')
            return redirect(url_for('financial.edit_record', record_id=record_id))
    cur.execute('''UPDATE financial_records SET crop_name=%s, season=%s, seeds_cost=%s, fertilizer_cost=%s, pesticides_cost=%s, irrigation_cost=%s, labour_cost=%s, machinery_cost=%s, other_expenses=%s, total_production=%s, selling_price=%s
                   WHERE id=%s AND farmer_id=%s''',
                (crop_name, season or None, seeds, fertilizer, pesticides, irrigation, labour, machinery, other, production, selling_price, record_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('Record updated.', 'success')
    return redirect(url_for('financial.dashboard'))

@financial_bp.route('/delete/<int:record_id>', methods=['POST'])
@farmer_required
def delete_record(record_id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM financial_records WHERE id = %s AND farmer_id = %s', (record_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('Record deleted.', 'success')
    return redirect(url_for('financial.dashboard'))

@financial_bp.route('/download/csv')
@farmer_required
def download_csv():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM financial_records WHERE farmer_id = %s ORDER BY created_at DESC', (session['user_id'],))
    records = cur.fetchall()
    cur.close()
    records = _compute_totals(records)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Crop Name', 'Season', 'Seeds Cost', 'Fertilizer Cost', 'Pesticides Cost', 'Irrigation Cost',
        'Labour Cost', 'Machinery Cost', 'Other Expenses', 'Total Expense', 'Total Production', 'Selling Price',
        'Total Income', 'Net Profit', 'Status', 'Created At'
    ])
    for r in records:
        writer.writerow([
            r.get('crop_name', ''),
            r.get('season', ''),
            r.get('seeds_cost', 0),
            r.get('fertilizer_cost', 0),
            r.get('pesticides_cost', 0),
            r.get('irrigation_cost', 0),
            r.get('labour_cost', 0),
            r.get('machinery_cost', 0),
            r.get('other_expenses', 0),
            float(r['total_expense']),
            r.get('total_production', 0),
            r.get('selling_price', 0),
            float(r['total_income']),
            float(r['net_profit']),
            r.get('status', ''),
            str(r.get('created_at', ''))
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=financial_records.csv'}
    )
