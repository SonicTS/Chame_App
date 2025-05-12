from flask import Flask, jsonify, render_template, request, redirect, url_for
from models.user_table import User
from models.product_table import Product
from models.sales_table import Sale
from chame_app.database import SessionLocal
from chame_app.database_instance import database
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../frontend/admin_webpage/templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../frontend/admin_webpage/static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

db_session = SessionLocal()
# Example route: Admin dashboard
@app.route('/')
def index():
    return render_template('admin_dashboard.html')  # Will render the admin dashboard HTML

# Example route: View all products
@app.route('/products')
def products():
    products = database.get_all_products()  # Fetch all products from the database
    return render_template('products.html', products=products)

# Example route: Add a product
@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        ingredients_ids = request.form.getlist('ingredients[]')
        ingredients = database.get_ingredients_by_ids(ingredients_ids)
            
        quantities = request.form.getlist('quantities[]')
        ingredient_quantity_pairs = list(zip(ingredients, quantities))

        # Add the product to the database
        database.add_product(name=name, ingredients=ingredient_quantity_pairs, price_per_unit=price, category=category)
        return redirect(url_for('products'))

    # Fetch all ingredients to display in the dropdown
    ingredients = database.get_all_ingredients()
    return render_template('add_product.html', ingredients=ingredients)


@app.route('/users/add', methods=['POST'])
def add_user():
    data = request.get_json()
    name = data.get('name')
    balance = data.get('balance')
    role = data.get('role')

    if not name or balance is None or not role:
        return jsonify({"error": "Invalid input"}), 400


    try:
        database.add_user(name=name, balance=balance, role=role)
        return jsonify({"message": "User added successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Example route: View all users
@app.route('/users')
def users():
    users = database.get_all_users()
    return render_template('users.html', users=users)

@app.route('/ingredients')
def ingredients():
    ingredients = database.get_all_ingredients()
    return render_template('ingredients.html', ingredients=ingredients)

@app.route('/ingredients/add', methods=['GET', 'POST'])
def add_ingredient():
    if request.method == 'POST':
        name = request.form['name']
        price_str = request.form['price']
        stock_str = request.form['stock']
        try:
            database.add_ingredient(name=name, price_per_unit=price_str, stock_quantity=stock_str)
            return redirect(url_for('ingredients'))
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return render_template('add_ingredient.html')

@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    if request.method == 'POST':
        user_id = request.form.get('userSelect')
        product_id = request.form.get('productSelect')
        quantity = request.form['quantity']
        try:
            database.make_purchase(user_id=user_id, product_id=product_id, quantity=quantity)
            return redirect(url_for('index'))
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    users = database.get_all_users()
    products = database.get_all_products()
    return render_template('purchase.html', users=users, products=products)


# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)