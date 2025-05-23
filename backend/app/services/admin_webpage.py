from flask import Flask, json, render_template, request, redirect, url_for
from models.user_table import User
from models.product_table import Product
from models.sales_table import Sale
from chame_app.database import SessionLocal
from chame_app.database_instance import database
import os
import logging
import sys
from markupsafe import Markup
import json as pyjson

# Configure logging
logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)

def escapejs_filter(value):
    """Escape string for safe use in JavaScript in Jinja2 templates."""
    if value is None:
        return ''
    return Markup(pyjson.dumps(str(value)))[1:-1]

app.jinja_env.filters['escapejs'] = escapejs_filter

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

# Template constants to avoid duplication
ADMIN_DASHBOARD_TEMPLATE = 'admin_dashboard.html'
PRODUCTS_TEMPLATE = 'products.html'
ADD_PRODUCT_TEMPLATE = 'add_product.html'
USERS_TEMPLATE = 'users.html'
INGREDIENTS_TEMPLATE = 'ingredients.html'
ADD_INGREDIENT_TEMPLATE = 'add_ingredient.html'
PURCHASE_TEMPLATE = 'purchase.html'
TOAST_ROUND_TEMPLATE = 'toast_round.html'
BANK_TEMPLATE = 'bank.html'

@app.route('/')
def index():
    try:
        logging.info("Admin dashboard accessed.")
        return render_template(ADMIN_DASHBOARD_TEMPLATE)
    except Exception as e:
        logging.error(f"Error in index: {e}", exc_info=e)
        return render_template(ADMIN_DASHBOARD_TEMPLATE, error_message=str(e))

@app.route('/products')
def products():
    try:
        products = database.get_all_products()  # Fetch all products from the database
        return render_template(PRODUCTS_TEMPLATE, products=products)
    except Exception as e:
        logging.error(f"Error in products: {e}", exc_info=e)
        return render_template(PRODUCTS_TEMPLATE, products=[], error_message=str(e))

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    try:
        if request.method == 'POST':
            name = request.form['name']
            category = request.form['category']
            price = request.form['price']
            ingredients_ids = request.form.getlist('ingredients[]')
            toaster_space = request.form.get('toaster_space')
            ingredients = database.get_ingredients_by_ids(ingredients_ids)
            quantities = request.form.getlist('quantities[]')
            ingredient_quantity_pairs = list(zip(ingredients, quantities))
            try:
                database.add_product(name=name, ingredients=ingredient_quantity_pairs, price_per_unit=price, category=category, toaster_space=toaster_space)
                return redirect(url_for('products'))
            except Exception as e:
                logging.error(f"Error adding product: {e}", exc_info=e)
                ingredients = database.get_all_ingredients()
                return render_template(ADD_PRODUCT_TEMPLATE, ingredients=ingredients, error_message=str(e))
        ingredients = database.get_all_ingredients()
        return render_template(ADD_PRODUCT_TEMPLATE, ingredients=ingredients)
    except Exception as e:
        logging.error(f"Error in add_product: {e}", exc_info=e)
        return render_template(ADD_PRODUCT_TEMPLATE, ingredients=[], error_message=str(e))

@app.route('/users/add', methods=['POST'])
def add_user():
    name = request.form['name']
    balance = request.form['balance']
    role = request.form['role']

    if not name or balance is None or not role:
        users = database.get_all_users()
        logging.error("Invalid input in add_user")
        return render_template(USERS_TEMPLATE, users=users, error_message="Invalid input")

    try:
        database.add_user(username=name, password="", balance=balance, role=role)
        return redirect(url_for('users'))
    except Exception as e:
        logging.error(f"Error in add_user: {e}", exc_info=e)
        users = database.get_all_users()
        return render_template(USERS_TEMPLATE, users=users, error_message=str(e))
    
@app.route('/users/withdraw', methods=['POST'])
def withdraw():
    user_id = request.form['user_id']
    amount = request.form['amount']

    if not user_id or not amount:
        users = database.get_all_users()
        logging.error("Invalid input in withdraw")
        return render_template(USERS_TEMPLATE, users=users, error_message="Invalid input")

    try:
        database.withdraw_cash(user_id=user_id, amount=amount)
        return redirect(url_for('users'))
    except Exception as e:
        logging.error(f"Error in withdraw: {e}", exc_info=e)
        users = database.get_all_users()
        transactions = database.get_filtered_transaction(user_id="all", tx_type="all")  # Replace with actual query result
        tx_list = []
        for tx in transactions:
            tx_list.append({
                "date": tx.timestamp,  # or tx.date if that's your field
                "user_name": tx.user.name if tx.user else "",  # assumes you set up the relationship
                "type": tx.type,
                "amount": tx.amount
            })
        return render_template(USERS_TEMPLATE, users=users, transactions=tx_list, error_message=str(e))
    

    
@app.route('/users/deposit', methods=['POST'])
def deposit():
    user_id = request.form['user_id']
    amount = request.form['amount']

    if not user_id or not amount:
        users = database.get_all_users()
        logging.error("Invalid input in withdraw")
        return render_template(USERS_TEMPLATE, users=users, error_message="Invalid input")

    try:
        database.deposit_cash(user_id=user_id, amount=amount)
        return redirect(url_for('users'))
    except Exception as e:
        logging.error(f"Error in withdraw: {e}", exc_info=e)
        users = database.get_all_users()
        transactions = database.get_filtered_transaction(user_id="all", tx_type="all")  # Replace with actual query result
        tx_list = []
        for tx in transactions:
            tx_list.append({
                "date": tx.timestamp,  # or tx.date if that's your field
                "user_name": tx.user.name if tx.user else "",  # assumes you set up the relationship
                "type": tx.type,
                "amount": tx.amount
            })
        return render_template(USERS_TEMPLATE, users=users, transactions=tx_list, error_message=str(e))
    
@app.route('/users/transactions')
def users_transactions():
    user_id = request.args.get('user_id', 'all')
    tx_type = request.args.get('type', 'all')
    # TODO: Query the database for transactions filtered by user_id and tx_type
    # Example: transactions = database.get_transactions(user_id=user_id, tx_type=tx_type)
    # The result should be a list of dicts with keys: date, user_name, type, amount
    transactions = database.get_filtered_transaction(user_id=user_id, tx_type=tx_type)  # Replace with actual query result
    tx_list = []
    for tx in transactions:
        tx_list.append({
            "date": tx.timestamp,  # or tx.date if that's your field
            "user_name": tx.user.name if tx.user else "",  # assumes you set up the relationship
            "type": tx.type,
            "amount": tx.amount
        })

    return app.response_class(
        response=pyjson.dumps(tx_list),
        status=200,
        mimetype='application/json'
    )

@app.route('/users')
def users():
    try:
        users = database.get_all_users()
        transactions = database.get_filtered_transaction(user_id="all", tx_type="all")  # Replace with actual query result
        tx_list = []
        for tx in transactions:
            tx_list.append({
                "date": tx.timestamp,  # or tx.date if that's your field
                "user_name": tx.user.name if tx.user else "",  # assumes you set up the relationship
                "type": tx.type,
                "amount": tx.amount
            })
        return render_template(USERS_TEMPLATE, users=users, transactions=tx_list)
    except Exception as e:
        logging.error(f"Error in users: {e}", exc_info=e)
        return render_template(USERS_TEMPLATE, users=[], error_message=str(e))

@app.route('/ingredients')
def ingredients():
    try:
        ingredients = database.get_all_ingredients(eager_load=True)
        return render_template(INGREDIENTS_TEMPLATE, ingredients=ingredients)
    except Exception as e:
        logging.error(f"Error in ingredients: {e}", exc_info=e)
        return render_template(INGREDIENTS_TEMPLATE, ingredients=[], error_message=str(e))

@app.route('/ingredients/add', methods=['GET', 'POST'])
def add_ingredient():
    try:
        if request.method == 'POST':
            name = request.form['name']
            price_str = request.form['price']
            stock_str = request.form['stock']
            number_ingredients = request.form['number_ingredients']
            try:
                database.add_ingredient(name=name, price_per_package=price_str, stock_quantity=stock_str, number_ingredients=number_ingredients)
                return redirect(url_for('ingredients'))
            except Exception as e:
                logging.error(f"Error adding ingredient: {e}", exc_info=e)
                return render_template(ADD_INGREDIENT_TEMPLATE, error_message=str(e))
        return render_template(ADD_INGREDIENT_TEMPLATE)
    except Exception as e:
        logging.error(f"Error in add_ingredient: {e}", exc_info=e)
        return render_template(ADD_INGREDIENT_TEMPLATE, error_message=str(e))

@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    try:
        if request.method == 'POST':
            user_id = request.form.get('user_id')
            product_id = request.form.get('product_id')
            quantity = request.form['quantity']
            try:
                database.make_purchase(user_id=user_id, product_id=product_id, quantity=quantity)
                return redirect(url_for('purchase'))
            except Exception as e:
                logging.error(f"Error making purchase: {e}", exc_info=e)
                return render_template(PURCHASE_TEMPLATE, users=database.get_all_users(), products=database.get_all_products(), sales=database.get_all_sales(), error_message=str(e))
        users = database.get_all_users()
        products = database.get_all_products()
        config = request.args.get('config', 'all')
        sales = database.get_all_sales()
        if config == 'raw':
            sales = database.get_sales_with_category(category='raw')
        elif config == 'toast':
            sales = database.get_sales_with_category(category='toast')
        return render_template(PURCHASE_TEMPLATE, users=users, products=products, sales=sales)
    except Exception as e:
        logging.error(f"Error in purchase: {e}", exc_info=e)
        return render_template(PURCHASE_TEMPLATE, users=[], products=[], sales=[], error_message=str(e))

@app.route('/toast_round', methods=['GET', 'POST'])
def toast_round():
    try:
        if request.method == 'POST':
            try:
                product_ids = request.form.getlist('product_ids[]')
                user_selections = request.form.getlist('user_selections[]')
                if not product_ids or not user_selections:
                    raise ValueError("Product IDs and user selections cannot be empty.")
                if len(product_ids) != len(user_selections):
                    raise ValueError("Mismatch between product IDs and user selections.")
                product_user_pairs = list(zip(product_ids, user_selections))
                database.add_toast_round(product_user_list=product_user_pairs)
            except Exception as e:
                logging.error(f"Error in toast_round POST: {e}", exc_info=e)
                toasts = database.get_all_toast_products()
                users = database.get_all_users()
                users_json = pyjson.dumps([{"user_id": user.user_id, "name": user.name} for user in users])
                toasts_json = pyjson.dumps([{"product_id": t.product_id, "name": t.name, "toaster_space": getattr(t, 'toaster_space', 1)} for t in toasts])
                toast_rounds = database.get_all_toast_rounds()
                return render_template(TOAST_ROUND_TEMPLATE, toast_rounds=toast_rounds, users_json=users_json, products_json=toasts_json, error_message=str(e))
        toasts = database.get_all_toast_products()
        users = database.get_all_users()
        users_json = pyjson.dumps([{"user_id": user.user_id, "name": user.name} for user in users])
        toasts_json = pyjson.dumps([{"product_id": t.product_id, "name": t.name, "toaster_space": getattr(t, 'toaster_space', 1)} for t in toasts])
        toast_rounds = database.get_all_toast_rounds()
        return render_template(TOAST_ROUND_TEMPLATE, toast_rounds=toast_rounds, users_json=users_json, products_json=toasts_json)
    except Exception as e:
        logging.error(f"Error in toast_round: {e}", exc_info=e)
        return render_template(TOAST_ROUND_TEMPLATE, toast_rounds=[], users_json='[]', products_json='[]', error_message=str(e))

@app.route('/ingredients/restock', methods=['POST'])
def restock_ingredient():
    ingredient_id = request.form['ingredient_id']
    quantity = request.form['restock_quantity']
    try:
        database.stock_ingredient(ingredient_id=ingredient_id, quantity=quantity)
        ingredients = database.get_all_ingredients(eager_load=True)
        return render_template(INGREDIENTS_TEMPLATE, ingredients=ingredients, success_message='Ingredient restocked successfully!')
    except Exception as e:
        logging.error(f"Error in restock_ingredient: {e}", exc_info=e)
        ingredients = database.get_all_ingredients(eager_load=True)
        return render_template(INGREDIENTS_TEMPLATE, ingredients=ingredients, transactions=None, error_message=str(e))

@app.route('/bank', methods=['GET'])
def bank():
    try:
        transactions = database.get_bank_transaction()  # Replace with actual query result
        tx_list = []
        for tx in transactions:
            tx_list.append({
                "date": tx.timestamp,  # or tx.date if that's your field
                "type": tx.type,
                "amount": tx.amount,
                "description": tx.description
            })
        bank = database.get_bank()
        return render_template(BANK_TEMPLATE, bank_entry=bank, transactions=tx_list)
    except Exception as e:
        logging.error(f"Error in bank: {e}", exc_info=e)
        return render_template(BANK_TEMPLATE, bank_entry=None, transactions=None, error_message=str(e))
    
@app.route('/bank/withdraw', methods=['POST'])
def bank_withdraw():
    amount = request.form['amount']
    description = request.form['description']
    if not amount:
        bank = database.get_bank()
        logging.error("Invalid input in bank withdraw")
        transactions = database.get_bank_transaction()  # Replace with actual query result
        tx_list = []
        for tx in transactions:
            tx_list.append({
                "date": tx.timestamp,  # or tx.date if that's your field
                "type": tx.type,
                "amount": tx.amount,
                "description": tx.description
            })
        return render_template(BANK_TEMPLATE, bank_entry=bank, transactions=tx_list, error_message="Invalid input")
    try:
        database.withdraw_cash_from_bank(amount=amount, description=description)
        return redirect(url_for('bank'))
    except Exception as e:
        logging.error(f"Error in bank withdraw: {e}", exc_info=e)
        bank = database.get_bank()
        transactions = database.get_bank_transaction()  # Replace with actual query result
        tx_list = []
        for tx in transactions:
            tx_list.append({
                "date": tx.timestamp,  # or tx.date if that's your field
                "type": tx.type,
                "amount": tx.amount,
                "description": tx.description
            })
        return render_template(BANK_TEMPLATE, bank_entry=bank, transactions=tx_list, error_message=str(e))



# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)