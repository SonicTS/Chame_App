#!/usr/bin/env python3
"""
Test script to verify Firebase logging setup
"""
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_firebase_logging():
    """Test Firebase logging utility"""
    print("Testing Firebase logging utility...")
    
    # Test without Flutter environment
    print("\n=== Test 1: Without Flutter environment ===")
    from utils.firebase_logger import log_info, log_warn, log_error, log_debug
    
    log_info("Test info message without Flutter")
    log_warn("Test warning message without Flutter")
    log_error("Test error message without Flutter")
    log_debug("Test debug message without Flutter")
    
    # Test with simulated Flutter environment
    print("\n=== Test 2: With simulated Flutter environment ===")
    os.environ['FLUTTER_ENV'] = 'true'
    
    # Reload the module to pick up the environment change
    import importlib
    import utils.firebase_logger
    importlib.reload(utils.firebase_logger)
    
    from utils.firebase_logger import log_info, log_warn, log_error, log_debug
    
    log_info("Test info message with Flutter env", {"test_data": "value"})
    log_warn("Test warning message with Flutter env", {"warning_level": "low"})
    log_error("Test error message with Flutter env", {"error_code": 123})
    log_debug("Test debug message with Flutter env", {"debug_info": True})
    
    print("\n=== Test 3: Model to_dict methods ===")
    
    # Test model to_dict methods with logging
    from models.user_table import User
    from models.product_table import Product
    from models.ingredient import Ingredient
    from models.toast_round import ToastRound
    
    # Create test instances with minimal data
    try:
        user = User(name="Test User", balance=10.0, role="user")
        user.user_id = 1  # Simulate an ID
        user.sales = []  # Empty sales to avoid DB queries
        
        print("Testing User.to_dict()...")
        user_dict = user.to_dict(include_sales=True)
        print(f"User dict: {user_dict}")
        
    except Exception as e:
        print(f"User test failed: {e}")
    
    try:
        product = Product(name="Test Product", category="test", price_per_unit=5.0)
        product.product_id = 1
        product.product_ingredients = []
        product.sales = []
        product.product_toast_rounds = []
        
        print("Testing Product.to_dict()...")
        product_dict = product.to_dict(include_ingredients=True, include_sales=True)
        print(f"Product dict: {product_dict}")
        
    except Exception as e:
        print(f"Product test failed: {e}")
    
    try:
        ingredient = Ingredient(name="Test Ingredient", price_per_unit=2.0)
        ingredient.ingredient_id = 1
        ingredient.ingredient_products = []
        
        print("Testing Ingredient.to_dict()...")
        ingredient_dict = ingredient.to_dict(include_products=True)
        print(f"Ingredient dict: {ingredient_dict}")
        
    except Exception as e:
        print(f"Ingredient test failed: {e}")
    
    try:
        toast_round = ToastRound()
        toast_round.toast_round_id = 1
        toast_round.toast_round_products = []
        toast_round.sales = []
        
        print("Testing ToastRound.to_dict()...")
        toast_round_dict = toast_round.to_dict(include_products=True, include_sales=True)
        print(f"ToastRound dict: {toast_round_dict}")
        
    except Exception as e:
        print(f"ToastRound test failed: {e}")
    
    print("\n=== All tests completed ===")

if __name__ == "__main__":
    test_firebase_logging()
