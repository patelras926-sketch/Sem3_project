# Farm Store: products (admin CRUD), farmer cart & checkout & billing
import json
from decimal import Decimal
from flask import Blueprint, request, redirect, url_for, render_template, flash, session
from db import mysql
from config import Config
from auth_utils import farmer_required, admin_required
from validators import validate_required_string, validate_positive_number, validate_decimal_range

store_bp = Blueprint('store', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# ---------- Farmer: product list ----------
@store_bp.route('/')
@farmer_required
def product_list():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM products WHERE stock > 0 ORDER BY name')
    products = cur.fetchall()
    cur.close()
    return render_template('farmer/store_list.html', products=products)

# ---------- Farmer: product detail ----------
@store_bp.route('/product/<int:product_id>')
@farmer_required
def product_detail(product_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cur.fetchone()
    cur.close()
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('store.product_list'))
    return render_template('farmer/store_product_detail.html', product=product)

# ---------- Farmer: add to cart ----------
@store_bp.route('/cart/add', methods=['POST'])
@farmer_required
def cart_add():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    if not product_id or quantity < 1:
        return redirect(url_for('store.product_list'))
    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO cart (farmer_id, product_id, quantity) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE quantity = quantity + %s',
                (session['user_id'], product_id, quantity, quantity))
    mysql.connection.commit()
    cur.close()
    flash('Added to cart.', 'success')
    return redirect(request.referrer or url_for('store.product_list'))

# ---------- Farmer: view cart ----------
@store_bp.route('/cart')
@farmer_required
def cart_view():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT c.id, c.product_id, c.quantity, p.name, p.price, p.discount, p.image_path, p.stock
                   FROM cart c JOIN products p ON p.id = c.product_id WHERE c.farmer_id = %s''', (session['user_id'],))
    items = cur.fetchall()
    cur.close()
    return render_template('farmer/cart.html', items=items)

# ---------- Farmer: update cart quantity ----------
@store_bp.route('/cart/update', methods=['POST'])
@farmer_required
def cart_update():
    cart_id = request.form.get('cart_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    if cart_id and quantity >= 0:
        cur = mysql.connection.cursor()
        if quantity == 0:
            cur.execute('DELETE FROM cart WHERE id = %s AND farmer_id = %s', (cart_id, session['user_id']))
        else:
            cur.execute('UPDATE cart SET quantity = %s WHERE id = %s AND farmer_id = %s', (quantity, cart_id, session['user_id']))
        mysql.connection.commit()
        cur.close()
    return redirect(url_for('store.cart_view'))

# ---------- Farmer: checkout & create order ----------
@store_bp.route('/checkout', methods=['GET', 'POST'])
@farmer_required
def checkout():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT c.id, c.product_id, c.quantity, p.name, p.price, p.discount, p.stock
                   FROM cart c JOIN products p ON p.id = c.product_id WHERE c.farmer_id = %s''', (session['user_id'],))
    items = cur.fetchall()
    if not items:
        cur.close()
        flash('Cart is empty.', 'warning')
        return redirect(url_for('store.product_list'))
    # Check stock
    for it in items:
        if it['quantity'] > it['stock']:
            flash(f'Insufficient stock for {it["name"]}.', 'danger')
            cur.close()
            return redirect(url_for('store.cart_view'))
    if request.method == 'GET':
        cur.execute('SELECT name FROM users WHERE id = %s', (session['user_id'],))
        user = cur.fetchone()
        # Calculate totals for display
        subtotal = Decimal('0')
        for it in items:
            price = Decimal(str(it['price'])) * (1 - Decimal(str(it['discount'] or 0)) / 100)
            subtotal += price * it['quantity']
        gst = subtotal * Decimal('0.05')
        total = subtotal + gst
        cur.close()
        return render_template('farmer/checkout.html', items=items, user=user, subtotal=subtotal, gst=gst, total=total)
    # POST: create order
    subtotal = Decimal('0')
    for it in items:
        price = Decimal(str(it['price'])) * (1 - Decimal(str(it['discount'] or 0)) / 100)
        subtotal += price * it['quantity']
    gst = subtotal * Decimal('0.05')  # 5% GST
    total = subtotal + gst
    cur.execute('INSERT INTO orders (farmer_id, subtotal, gst, total, status) VALUES (%s, %s, %s, %s, %s)',
                (session['user_id'], float(subtotal), float(gst), float(total), 'Completed'))
    order_id = cur.lastrowid
    for it in items:
        price = Decimal(str(it['price'])) * (1 - Decimal(str(it['discount'] or 0)) / 100)
        cur.execute('INSERT INTO order_items (order_id, product_id, quantity, price_per_unit) VALUES (%s, %s, %s, %s)',
                    (order_id, it['product_id'], it['quantity'], float(price)))
        cur.execute('UPDATE products SET stock = stock - %s WHERE id = %s', (it['quantity'], it['product_id']))
    cur.execute('DELETE FROM cart WHERE farmer_id = %s', (session['user_id'],))
    mysql.connection.commit()
    cur.close()
    flash('Order placed successfully.', 'success')
    return redirect(url_for('store.order_history'))

# ---------- Farmer: order invoice ----------
@store_bp.route('/order/<int:order_id>')
@farmer_required
def order_invoice(order_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM orders WHERE id = %s AND farmer_id = %s', (order_id, session['user_id']))
    order = cur.fetchone()
    if not order:
        cur.close()
        flash('Order not found.', 'danger')
        return redirect(url_for('store.order_history'))
    cur.execute('SELECT oi.*, p.name FROM order_items oi JOIN products p ON p.id = oi.product_id WHERE oi.order_id = %s', (order_id,))
    items = cur.fetchall()
    cur.close()
    return render_template('farmer/invoice.html', order=order, items=items)

# ---------- Farmer: order history ----------
@store_bp.route('/orders')
@farmer_required
def order_history():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM orders WHERE farmer_id = %s ORDER BY order_date DESC', (session['user_id'],))
    orders = cur.fetchall()
    cur.close()
    return render_template('farmer/order_history.html', orders=orders)

# ---------- Admin: product list ----------
@store_bp.route('/admin')
@admin_required
def admin_list():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM products ORDER BY name')
    products = cur.fetchall()
    cur.close()
    return render_template('admin/products_list.html', products=products)

# ---------- Admin: add product ----------
@store_bp.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def admin_add():
    if request.method == 'GET':
        return render_template('admin/product_form.html', product=None)
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'Fertilizers')
    brand = request.form.get('brand', '').strip()
    description = request.form.get('description', '').strip()
    price = request.form.get('price') or 0
    discount = request.form.get('discount') or 0
    stock = request.form.get('stock') or 0
    usage_crops = request.form.get('usage_crops', '').strip()
    nutrient = request.form.get('nutrient_composition', '').strip()
    ok, err = validate_required_string(name, 'Product name', max_len=200)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('store.admin_add'))
    ok, err = validate_positive_number(price, 'Price', required=True)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('store.admin_add'))
    ok, err = validate_decimal_range(discount, 'Discount', min_val=0, max_val=100, required=False)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('store.admin_add'))
    ok, err = validate_positive_number(stock, 'Stock', required=False)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('store.admin_add'))
    image_path = None
    f = request.files.get('product_image')
    if f and f.filename and allowed_file(f.filename):
        path = Config.PRODUCT_IMAGES_FOLDER / f.filename
        f.save(str(path))
        image_path = f'uploads/products/{f.filename}'
    cur = mysql.connection.cursor()
    cur.execute('''INSERT INTO products (name, image_path, category, brand, description, price, discount, stock, usage_crops, nutrient_composition)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (name, image_path, category, brand or None, description or None, price, discount, stock, usage_crops or None, nutrient or None))
    mysql.connection.commit()
    cur.close()
    flash('Product added.', 'success')
    return redirect(url_for('store.admin_list'))

# ---------- Admin: edit product ----------
@store_bp.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit(product_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cur.fetchone()
    if not product:
        cur.close()
        flash('Product not found.', 'danger')
        return redirect(url_for('store.admin_list'))
    if request.method == 'GET':
        cur.close()
        return render_template('admin/product_form.html', product=product)
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'Fertilizers')
    brand = request.form.get('brand', '').strip()
    description = request.form.get('description', '').strip()
    price = request.form.get('price') or 0
    discount = request.form.get('discount') or 0
    stock = request.form.get('stock') or 0
    usage_crops = request.form.get('usage_crops', '').strip()
    nutrient = request.form.get('nutrient_composition', '').strip()
    ok, err = validate_required_string(name, 'Product name', max_len=200)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('store.admin_edit', product_id=product_id))
    ok, err = validate_positive_number(price, 'Price', required=True)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('store.admin_edit', product_id=product_id))
    ok, err = validate_decimal_range(discount, 'Discount', min_val=0, max_val=100, required=False)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('store.admin_edit', product_id=product_id))
    ok, err = validate_positive_number(stock, 'Stock', required=False)
    if not ok:
        flash(err, 'danger')
        return redirect(url_for('store.admin_edit', product_id=product_id))
    image_path = product.get('image_path')
    f = request.files.get('product_image')
    if f and f.filename and allowed_file(f.filename):
        path = Config.PRODUCT_IMAGES_FOLDER / f.filename
        f.save(str(path))
        image_path = f'uploads/products/{f.filename}'
    cur.execute('''UPDATE products SET name=%s, image_path=%s, category=%s, brand=%s, description=%s, price=%s, discount=%s, stock=%s, usage_crops=%s, nutrient_composition=%s WHERE id=%s''',
                (name, image_path, category, brand or None, description or None, price, discount, stock, usage_crops or None, nutrient or None, product_id))
    mysql.connection.commit()
    cur.close()
    flash('Product updated.', 'success')
    return redirect(url_for('store.admin_list'))

# ---------- Admin: delete product ----------
@store_bp.route('/admin/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete(product_id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM products WHERE id = %s', (product_id,))
    mysql.connection.commit()
    cur.close()
    flash('Product deleted.', 'success')
    return redirect(url_for('store.admin_list'))
