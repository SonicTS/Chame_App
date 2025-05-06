from flask import Flask, jsonify, render_template, request, redirect, url_for
from models.user_table import User
from models.product_table import Product
from models.sales_table import Sale
from chame_app.database import SessionLocal
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../frontend/admin_webpage/templates'))
app = Flask(__name__, template_folder=template_dir)

db_session = SessionLocal()
# Example route: Admin dashboard
@app.route('/')
def index():
    return render_template('admin_dashboard.html')  # Will render the admin dashboard HTML

# Example route: View all products
@app.route('/products')
def products():
    products = db_session.query(Product).all()
    return render_template('products.html', products=products)

# Example route: Add a product
@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        stock = request.form['stock']
        new_product = Product(name=name, category=category, price_per_unit=price, stock_quantity=stock)
        db_session.add(new_product)
        db_session.commit()
        return redirect(url_for('products'))  # Redirect to product listing after adding

    return render_template('add_product.html')  # A form to add a product


@app.route('/users/add', methods=['POST'])
def add_user():
    data = request.get_json()
    name = data.get('name')
    balance = data.get('balance')
    role = data.get('role')

    if not name or balance is None or not role:
        return jsonify({"error": "Invalid input"}), 400

    db_session = SessionLocal()
    try:
        # Add the new user to the database
        new_user = User(name=name, balance=balance, role=role)
        db_session.add(new_user)
        db_session.commit()
        return jsonify({"message": "User added successfully"}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.close()

# Example route: View all users
@app.route('/users')
def users():
    users = db_session.query(User).all()
    return render_template('users.html', users=users)

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)