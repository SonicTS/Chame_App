from flask import Flask, json, jsonify, render_template, request, redirect, url_for
from models.user_table import User
from models.product_table import Product
from models.sales_table import Sale
from chame_app.database import SessionLocal
from chame_app.database_instance import database
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../frontend/admin_webpage/templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../frontend/admin_webpage/static'))
app = Flask(__name__)

def initialize_app_paths():
    """Set paths for templates and static files dynamically based on the environment."""
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a development environment
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../frontend/admin_webpage'))

    app.template_folder = os.path.join(base_path, 'templates')
    app.static_folder = os.path.join(base_path, 'static')

# Initialize paths
initialize_app_paths()

@app.errorhandler(Exception)
def handle_exception(e):
    """Log unhandled exceptions."""
    logging.error("Unhandled Exception", exc_info=e)
    return jsonify({"error": "An internal error occurred."}), 500

# Example route: Admin dashboard
@app.route('/')
def index():
    logging.info("Admin dashboard accessed.")
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
        toast_round_quantity = request.form.get('toast_round_quantity')
        ingredients = database.get_ingredients_by_ids(ingredients_ids)
            
        quantities = request.form.getlist('quantities[]')
        ingredient_quantity_pairs = list(zip(ingredients, quantities))

        # Add the product to the database
        database.add_product(name=name, ingredients=ingredient_quantity_pairs, price_per_unit=price, category=category, toast_round_quantity=toast_round_quantity)
        return redirect(url_for('products'))

    # Fetch all ingredients to display in the dropdown
    ingredients = database.get_all_ingredients()
    return render_template('add_product.html', ingredients=ingredients)


@app.route('/users/add', methods=['POST'])
def add_user():
    name = request.form['name']
    balance = request.form['balance']
    role = request.form['role']

    if not name or balance is None or not role:
        return jsonify({"error": "Invalid input"}), 400


    try:
        database.add_user(username=name, password="", balance=balance, role=role)
        return redirect(url_for('users'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Example route: View all users
@app.route('/users')
def users():
    users = database.get_all_users()
    return render_template('users.html', users=users)

@app.route('/ingredients')
def ingredients():
    ingredients = database.get_all_ingredients(eager_load=True)
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
        user_id = request.form.get('user_id')
        product_id = request.form.get('product_id')
        quantity = request.form['quantity']
        try:
            database.make_purchase(user_id=user_id, product_id=product_id, quantity=quantity)
            return redirect(url_for('index'))
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    users = database.get_all_users()
    products = database.get_all_products()
    config = request.args.get('config', 'all')
    sales = database.get_all_sales()
    if config == 'raw':
        sales = database.get_sales_with_category(category='raw')
    elif config == 'toast':
        sales = database.get_sales_with_category(category='toast')
    return render_template('purchase.html', users=users, products=products, sales=sales)

@app.route('/toast_round', methods=['GET', 'POST'])
def toast_round():
    if request.method == 'POST':
        try:
            # Parse the product ID and user selections from the form data
            product_id = request.form.get('product_id')
            user_selections = request.form.getlist('user_selections[]')

            # Perform backend logic (e.g., update database, process selections)
            for user_id in user_selections:
                # Example: Log the user and product association (replace with actual logic)
                print(f"User {user_id} selected for product {product_id}")

            # Return a success response
            database.add_toast_round(product_id=product_id, user_selection=user_selections)
        except Exception as e:
            # Handle errors and return an error response
            return jsonify({"error": str(e)}), 500

    toasts = database.get_all_toast_products()
    users = database.get_all_users()
    users_json = json.dumps([{"user_id": user.user_id, "name": user.name} for user in users])
    toast_rounds = database.get_all_toast_rounds()
    return render_template('toast_round.html', toast_products=toasts, users=users, users_json=users_json, toast_rounds=toast_rounds)

@app.route('/ingredients/restock', methods=['POST'])
def restock_ingredient():
    ingredient_id = request.form['ingredient_id']
    quantity = request.form['restock_quantity']
    try:
        database.stock_ingredient(ingredient_id=ingredient_id, quantity=quantity)
        return ingredients()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/bank', methods=['GET'])
def bank():
    # Fetch all bank entries from the database
    bank = database.get_bank()
    return render_template('bank.html', bank_entry=bank)

@app.route('/control_panel')
def control_panel():
    return render_template('control_panel.html')

@app.route('/stop_app')
def stop_app():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

@app.route('/shutdown', methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

@app.route('/admin_dashboard')
def admin_dashboard():
    return redirect('/')

# Example of logging in a route
@app.route('/example')
def example_route():
    logging.info("Example route accessed.")
    try:
        # Simulate some logic
        1 / 0  # This will raise an exception
    except Exception as e:
        logging.error("Error in example route", exc_info=e)
        return jsonify({"error": "An error occurred."}), 500
    return jsonify({"message": "Success"})

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)