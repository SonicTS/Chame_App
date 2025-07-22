# comprehensive_api_tests.py
# Complete testing framework for admin_api functions using generated test databases

import os
import sys
import tempfile
import shutil
import logging
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your modules
import services.admin_api as api

# Constants
NO_DATABASES_MSG = "❌ No test databases found"

logger = logging.getLogger(__name__)

class ComprehensiveAPITester:
    """Complete testing framework for all admin API functions using generated test databases"""
    
    def __init__(self, version=None, database_type=None):
        self.version = version
        self.database_type = database_type
        self.test_databases_dir = "testing/test_databases"
        self.temp_dir = None
        self.current_db_path = None
        self.available_versions = []
        self.available_databases = {}
        
    def setup_test_environment(self):
        """Set up temporary directory for testing"""
        self.temp_dir = tempfile.mkdtemp(prefix="api_test_")
        
        # Set environment variable to use test database
        os.environ["PRIVATE_STORAGE"] = self.temp_dir
        
        print(f"📁 Test environment created at: {self.temp_dir}")
        
    def teardown_test_environment(self):
        """Clean up test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up test environment: {self.temp_dir}")
    
    def discover_available_databases(self):
        """Discover all available test database versions and types"""
        test_db_path = Path(self.test_databases_dir)
        self.available_versions = []
        self.available_databases = {}
        
        if not test_db_path.exists():
            print(f"❌ Test databases directory not found: {self.test_databases_dir}")
            return False
        
        # Find all version directories
        for version_dir in test_db_path.iterdir():
            if version_dir.is_dir() and not version_dir.name.startswith('.'):
                # Check if directory contains .db files
                db_files = list(version_dir.glob("*.db"))
                if db_files:
                    version_name = version_dir.name
                    self.available_versions.append(version_name)
                    self.available_databases[version_name] = {}
                    
                    # Categorize databases by type
                    for db_file in db_files:
                        db_name = db_file.stem
                        if "minimal" in db_name:
                            self.available_databases[version_name]["minimal"] = str(db_file)
                        elif "comprehensive" in db_name:
                            self.available_databases[version_name]["comprehensive"] = str(db_file)
                        elif "edge" in db_name:
                            self.available_databases[version_name]["edge"] = str(db_file)
                        elif "performance" in db_name:
                            self.available_databases[version_name]["performance"] = str(db_file)
                        else:
                            # Generic database
                            self.available_databases[version_name]["generic"] = str(db_file)
        
        # Sort versions (newer versions should come last alphabetically if named properly)
        self.available_versions.sort()
        
        return len(self.available_versions) > 0
    
    def get_latest_version(self):
        """Get the latest available version"""
        if not self.available_versions:
            return None
        return self.available_versions[-1]
    
    def select_database(self):
        """Select appropriate database based on version and type preferences"""
        if not self.discover_available_databases():
            print("❌ No test databases found")
            return None
        
        print(f"📋 Found test database versions: {', '.join(self.available_versions)}")
        
        # Determine version to use
        selected_version = self.version
        if not selected_version:
            selected_version = self.get_latest_version()
            print(f"🎯 No version specified, using latest: {selected_version}")
        elif selected_version not in self.available_versions:
            print(f"⚠️ Requested version '{selected_version}' not found")
            selected_version = self.get_latest_version()
            print(f"🎯 Falling back to latest version: {selected_version}")
        else:
            print(f"🎯 Using specified version: {selected_version}")
        
        if not selected_version:
            return None
        
        # Determine database type to use
        available_types = list(self.available_databases[selected_version].keys())
        print(f"� Available database types in {selected_version}: {', '.join(available_types)}")
        
        selected_type = self.database_type
        if not selected_type:
            # Default preference order
            preference_order = ["comprehensive", "minimal", "edge", "performance", "generic"]
            for pref_type in preference_order:
                if pref_type in available_types:
                    selected_type = pref_type
                    break
            if not selected_type:
                selected_type = available_types[0]
            print(f"🎯 No database type specified, using: {selected_type}")
        elif selected_type not in available_types:
            print(f"⚠️ Requested database type '{selected_type}' not found in {selected_version}")
            selected_type = available_types[0]
            print(f"🎯 Falling back to: {selected_type}")
        else:
            print(f"🎯 Using specified database type: {selected_type}")
        
        selected_db_path = self.available_databases[selected_version][selected_type]
        print(f"✅ Selected database: {selected_db_path}")
        
        return selected_db_path
    
    def generate_missing_databases(self):
        """Generate test databases if none are available"""
        print("🔧 No test databases found, generating new ones...")
        
        try:
            import subprocess
            
            # Determine version to generate
            target_version = self.version or "v1.0"
            
            print(f"📦 Generating test databases for version: {target_version}")
            
            # Run the database generator
            result = subprocess.run([
                "python", "testing/generate_test_databases.py", "all", "--version", target_version
            ], capture_output=True, text=True, cwd=os.path.dirname(self.test_databases_dir))
            
            if result.returncode == 0:
                print("✅ Test databases generated successfully")
                print(f"📝 Generator output:\n{result.stdout}")
                
                # Re-discover databases
                if self.discover_available_databases():
                    return self.select_database()
                else:
                    print("❌ Failed to find generated databases")
                    return None
            else:
                print(f"❌ Database generation failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Error generating databases: {e}")
            return None
    
    def copy_database_to_test_env(self, source_db_path):
        """Copy selected database to test environment"""
        if not os.path.exists(source_db_path):
            raise FileNotFoundError(f"Source database not found: {source_db_path}")
        
        # Target path in test environment (standard name expected by admin_api)
        target_path = os.path.join(self.temp_dir, "kassensystem.db")
        
        # Copy database
        shutil.copy2(source_db_path, target_path)
        
        print(f"📄 Copied database: {os.path.basename(source_db_path)} -> test environment")
        self.current_db_path = target_path
        
        return target_path
    
    def analyze_test_database(self):
        """Analyze the current test database to understand its contents"""
        if not self.current_db_path:
            return
        
        print(f"📊 Analyzing test database: {os.path.basename(self.current_db_path)}")
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.current_db_path)
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print("📋 Database contents:")
            for table in sorted(tables):
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  • {table}: {count} records")
                except Exception as e:
                    print(f"  • {table}: Error counting records ({e})")
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Error analyzing database: {e}")
    
    def prepare_test_database(self):
        """Prepare test database for API testing"""
        # Select or generate database
        selected_db = self.select_database()
        
        if not selected_db:
            print("📦 Attempting to generate test databases...")
            selected_db = self.generate_missing_databases()
        
        if not selected_db:
            raise RuntimeError("No test databases available and generation failed")
        
        # Copy to test environment
        self.copy_database_to_test_env(selected_db)
        
        # Analyze database contents
        self.analyze_test_database()
        
        # Reset API database instance to use our test database
        api.database = None
        
        # Create database connection (this will use our copied database)
        db = api.create_database(False)
        
        print("✅ Test database prepared successfully")
        return db
    
    def _validate_user_dict(self, user_dict, test_results):
        """Validate that a user dictionary has the expected fields"""
        expected_fields = ['user_id', 'name', 'balance', 'role']
        return self._validate_dict_structure(user_dict, expected_fields, 'user', test_results)
    
    def _validate_product_dict(self, product_dict, test_results):
        """Validate that a product dictionary has the expected fields"""
        expected_fields = ['product_id', 'name', 'category', 'price_per_unit', 'cost_per_unit', 'profit_per_unit', 'stock_quantity', 'toaster_space']
        return self._validate_dict_structure(product_dict, expected_fields, 'product', test_results)
    
    def _validate_ingredient_dict(self, ingredient_dict, test_results):
        """Validate that an ingredient dictionary has the expected fields"""
        expected_fields = ['ingredient_id', 'name', 'price_per_package', 'number_of_units', 'pfand', 'price_per_unit', 'stock_quantity']
        return self._validate_dict_structure(ingredient_dict, expected_fields, 'ingredient', test_results)
    
    def _validate_sale_dict(self, sale_dict, test_results):
        """Validate that a sale dictionary has the expected fields"""
        expected_fields = ['sale_id', 'consumer_id', 'product_id', 'quantity', 'total_price', 'timestamp']
        return self._validate_dict_structure(sale_dict, expected_fields, 'sale', test_results)
    
    def _validate_transaction_dict(self, transaction_dict, test_results):
        """Validate that a transaction dictionary has the expected fields"""
        expected_fields = ['transaction_id', 'user_id', 'amount', 'type', 'timestamp']
        return self._validate_dict_structure(transaction_dict, expected_fields, 'transaction', test_results)
    
    def _validate_bank_dict(self, bank_dict, test_results):
        """Validate that a bank dictionary has the expected fields"""
        expected_fields = ['account_id', 'total_balance', 'customer_funds', 'revenue_funds']
        return self._validate_dict_structure(bank_dict, expected_fields, 'bank', test_results)
    
    def _validate_pfand_history_dict(self, pfand_dict, test_results):
        """Validate that a pfand history dictionary has the expected fields"""
        expected_fields = ['user_id', 'product_id', 'counter']
        return self._validate_dict_structure(pfand_dict, expected_fields, 'pfand_history', test_results)
    
    def _validate_toast_round_dict(self, toast_round_dict, test_results):
        """Validate that a toast round dictionary has the expected fields"""
        expected_fields = ['toast_round_id', 'timestamp']
        return self._validate_dict_structure(toast_round_dict, expected_fields, 'toast_round', test_results)
    
    def _validate_dict_structure(self, data_dict, expected_fields, entity_type, test_results):
        """Generic validation for dictionary structure"""
        if not isinstance(data_dict, dict):
            test_results['failed'] += 1
            test_results['errors'].append(f"{entity_type}: Expected dict, got {type(data_dict)}")
            return False
        
        missing_fields = [field for field in expected_fields if field not in data_dict]
        if missing_fields:
            test_results['failed'] += 1
            test_results['errors'].append(f"{entity_type}: Missing fields: {missing_fields}")
            return False
        
        # Check for unexpected None values in critical fields
        none_fields = [field for field in expected_fields if data_dict.get(field) is None and field.endswith('_id')]
        if none_fields:
            test_results['failed'] += 1
            test_results['errors'].append(f"{entity_type}: ID fields cannot be None: {none_fields}")
            return False
        
        return True
    
    def _validate_list_response(self, response, validator_func, entity_type, test_results, min_items=0):
        """Validate a list response from API"""
        if response is None:
            if min_items > 0:
                test_results['failed'] += 1
                test_results['errors'].append(f"{entity_type}: Expected list but got None")
                return False
            else:
                # None is acceptable for empty lists in some cases
                return True
        
        if not isinstance(response, list):
            test_results['failed'] += 1
            test_results['errors'].append(f"{entity_type}: Expected list, got {type(response)}")
            return False
        
        if len(response) < min_items:
            test_results['failed'] += 1
            test_results['errors'].append(f"{entity_type}: Expected at least {min_items} items, got {len(response)}")
            return False
        
        # Validate each item in the list
        for i, item in enumerate(response):
            if not validator_func(item, test_results):
                test_results['errors'].append(f"{entity_type}[{i}]: Structure validation failed")
                return False
        
        test_results['passed'] += 1
        print(f"  ✅ {entity_type} list: Structure validated ({len(response)} items)")
        return True
    
    def test_all_api_functions(self):
        """Test every function in the admin API"""
        print("\n🧪 Testing all admin API functions...")
        
        test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # Test data fetcher functions
        self._test_data_fetchers(test_results)
        
        # Test user management functions
        self._test_user_management(test_results)
        
        # Test ingredient management functions
        self._test_ingredient_management(test_results)
        
        # Test product management functions
        self._test_product_management(test_results)
        
        # Test purchase functions
        self._test_purchase_functions(test_results)
        
        # Test bank functions
        self._test_bank_functions(test_results)
        
        # Test authentication functions
        self._test_authentication_functions(test_results)
        
        # Test stock history functions
        self._test_stock_history_functions(test_results)
        
        # Test soft delete and deletion functions
        self._test_soft_delete_functions(test_results)
        
        return test_results
    
    def _test_function(self, func_name, func_call, test_results, expect_error=False):
        """Helper method to test a single function"""
        try:
            result = func_call()
            if expect_error:
                test_results['failed'] += 1
                test_results['errors'].append(f"{func_name}: Expected error but got result: {type(result)}")
                print(f"  ❌ {func_name}: Expected error but succeeded")
            else:
                test_results['passed'] += 1
                print(f"  ✅ {func_name}: Success (returned {type(result)})")
            return result
        except Exception as e:
            if expect_error:
                test_results['passed'] += 1
                print(f"  ✅ {func_name}: Expected error: {e}")
            else:
                test_results['failed'] += 1
                test_results['errors'].append(f"{func_name}: {str(e)}")
                print(f"  ❌ {func_name}: {e}")
            return None
    
    def _test_data_fetchers(self, test_results):
        """Test all data fetching functions and validate returned dictionary structures"""
        print("\n📊 Testing data fetcher functions...")
        
        # Test and validate users
        users = self._test_function("get_all_users", lambda: api.get_all_users(), test_results)
        if users is not None:
            self._validate_list_response(users, self._validate_user_dict, "users", test_results)
        
        # Test and validate products
        products = self._test_function("get_all_products", lambda: api.get_all_products(), test_results)
        if products is not None:
            self._validate_list_response(products, self._validate_product_dict, "products", test_results)
        
        # Test and validate ingredients
        ingredients = self._test_function("get_all_ingredients", lambda: api.get_all_ingredients(), test_results)
        if ingredients is not None:
            self._validate_list_response(ingredients, self._validate_ingredient_dict, "ingredients", test_results)
        
        # Test and validate sales
        sales = self._test_function("get_all_sales", lambda: api.get_all_sales(), test_results)
        if sales is not None:
            self._validate_list_response(sales, self._validate_sale_dict, "sales", test_results)
        
        # Test and validate toast products
        toast_products = self._test_function("get_all_toast_products", lambda: api.get_all_toast_products(), test_results)
        if toast_products is not None:
            self._validate_list_response(toast_products, self._validate_product_dict, "toast_products", test_results)
        
        # Test and validate toast rounds
        toast_rounds = self._test_function("get_all_toast_rounds", lambda: api.get_all_toast_rounds(), test_results)
        if toast_rounds is not None:
            self._validate_list_response(toast_rounds, self._validate_toast_round_dict, "toast_rounds", test_results)
        
        # Test and validate bank (single dict, not list)
        bank = self._test_function("get_bank", lambda: api.get_bank(), test_results)
        if bank is not None:
            if not self._validate_bank_dict(bank, test_results):
                test_results['errors'].append("bank: Structure validation failed")
            else:
                test_results['passed'] += 1
                print("  ✅ bank dict: Structure validated")
        
        # Test and validate bank transactions
        bank_transactions = self._test_function("get_bank_transaction", lambda: api.get_bank_transaction(), test_results)
        if bank_transactions is not None:
            # Bank transactions return a list with different structure - validate as generic dicts
            if isinstance(bank_transactions, list):
                test_results['passed'] += 1
                print(f"  ✅ bank_transaction list: Structure validated ({len(bank_transactions)} items)")
            else:
                test_results['failed'] += 1
                test_results['errors'].append(f"bank_transaction: Expected list, got {type(bank_transactions)}")
        
        # Test and validate pfand history
        pfand_history = self._test_function("get_pfand_history", lambda: api.get_pfand_history(), test_results)
        if pfand_history is not None:
            self._validate_list_response(pfand_history, self._validate_pfand_history_dict, "pfand_history", test_results)
        
        # Test and validate filtered transactions
        all_transactions = self._test_function("get_filtered_transaction (all)", 
                          lambda: api.get_filtered_transaction(), test_results)
        if all_transactions is not None:
            self._validate_list_response(all_transactions, self._validate_transaction_dict, "all_transactions", test_results)
        
        user1_transactions = self._test_function("get_filtered_transaction (user 1)", 
                          lambda: api.get_filtered_transaction(user_id=1), test_results)
        if user1_transactions is not None:
            self._validate_list_response(user1_transactions, self._validate_transaction_dict, "user1_transactions", test_results)
        
        sales_transactions = self._test_function("get_filtered_transaction (sales only)", 
                          lambda: api.get_filtered_transaction(tx_type="sale"), test_results)
        if sales_transactions is not None:
            self._validate_list_response(sales_transactions, self._validate_transaction_dict, "sales_transactions", test_results)
    
    def _test_user_management(self, test_results):
        """Test user management functions"""
        print("\n👥 Testing user management functions...")
        
        # Valid user creation
        self._test_function("add_user (valid regular)", 
                          lambda: api.add_user("test_user_new", 20.0, "user", 1), test_results)
        self._test_function("add_user (valid admin)", 
                          lambda: api.add_user("test_admin_new", 100.0, "admin", 1, "password123"), test_results)
        
        # Invalid user creation (should fail)
        self._test_function("add_user (invalid - no name)", 
                          lambda: api.add_user("", 20.0, "user", 1), test_results, expect_error=True)
        self._test_function("add_user (invalid - admin no password)", 
                          lambda: api.add_user("bad_admin", 100.0, "admin", 1, ""), test_results, expect_error=True)
        self._test_function("add_user (invalid - short admin password)", 
                          lambda: api.add_user("bad_admin2", 100.0, "admin", 1, "123"), test_results, expect_error=True)
        
        # Money operations
        users = api.get_all_users()
        if users:
            user_id = users[0]["user_id"]
            self._test_function("deposit", 
                              lambda: api.deposit(user_id, 10.0, 1), test_results)
            self._test_function("withdraw", 
                              lambda: api.withdraw(user_id, 5.0, 1), test_results)
            
            # Invalid money operations
            self._test_function("withdraw (insufficient funds)", 
                              lambda: api.withdraw(user_id, 99999.0, 1), test_results, expect_error=True)
            self._test_function("deposit (invalid amount)", 
                              lambda: api.deposit(user_id, -10.0, 1), test_results, expect_error=True)
    
    def _test_ingredient_management(self, test_results):
        """Test ingredient management functions"""
        print("\n🥬 Testing ingredient management functions...")
        
        # Valid ingredient creation
        self._test_function("add_ingredient (valid)", 
                          lambda: api.add_ingredient("Test_Ingredient_New", 3.50, 15, 8, 0.15), test_results)
        self._test_function("add_ingredient (no pfand)", 
                          lambda: api.add_ingredient("No_Pfand_Ingredient", 2.00, 20, 10, 0.0), test_results)
        
        # Invalid ingredient creation
        self._test_function("add_ingredient (invalid - no name)", 
                          lambda: api.add_ingredient("", 3.50, 15, 8, 0.15), test_results, expect_error=True)
        self._test_function("add_ingredient (invalid - no price)", 
                          lambda: api.add_ingredient("Bad_Ingredient", 0, 15, 8, 0.15), test_results, expect_error=True)
        
        # Restocking
        ingredients = api.get_all_ingredients()
        if ingredients:
            ingredient_id = ingredients[0]["ingredient_id"]
            self._test_function("restock_ingredient", 
                              lambda: api.restock_ingredient(ingredient_id, 10), test_results)
            
            # Bulk restocking
            restock_list = [{'id': ingredient_id, 'restock': 5}]
            self._test_function("restock_ingredients", 
                              lambda: api.restock_ingredients(restock_list, 1), test_results)
    
    def _test_product_management(self, test_results):
        """Test product management functions"""
        print("\n🍞 Testing product management functions...")
        
        ingredients = api.get_all_ingredients()
        if ingredients and len(ingredients) >= 2:
            ingredient_ids = [ingredients[0]["ingredient_id"], ingredients[1]["ingredient_id"]]
            quantities = [1, 2]
            
            # Valid product creation
            self._test_function("add_product (valid)", 
                              lambda: api.add_product("Test_Product_New", "test", 4.50, 
                                                     ingredient_ids, quantities, 1), test_results)
            
            # Invalid product creation
            self._test_function("add_product (invalid - no name)", 
                              lambda: api.add_product("", "test", 4.50, 
                                                     ingredient_ids, quantities, 1), test_results, expect_error=True)
            self._test_function("add_product (invalid - no ingredients)", 
                              lambda: api.add_product("Bad_Product", "test", 4.50, 
                                                     [], [], 1), test_results, expect_error=True)
    
    def _test_purchase_functions(self, test_results):
        """Test purchase-related functions"""
        print("\n💰 Testing purchase functions...")
        
        users = api.get_all_users()
        products = api.get_all_products()
        user_id = None
        if users and products:
            for user in users:
                if user['balance'] > products[0]['price_per_unit']:
                    # Use the first user with sufficient balance
                    user_id = user['user_id']
                    break
            if not user_id:
                print("⚠️ No user with sufficient balance found for purchases")
                return
            product_id = products[0]["product_id"]
            # Valid purchase
            self._test_function("make_purchase (valid)", 
                              lambda: api.make_purchase(user_id, product_id, 1, 1), test_results)
            
            # Invalid purchases
            self._test_function("make_purchase (invalid - no user)", 
                              lambda: api.make_purchase(0, product_id, 1, 1), test_results, expect_error=True)
            self._test_function("make_purchase (invalid - no product)", 
                              lambda: api.make_purchase(user_id, 0, 1, 1), test_results, expect_error=True)
            self._test_function("make_purchase (invalid - zero quantity)", 
                              lambda: api.make_purchase(user_id, product_id, 0, 1), test_results, expect_error=True)
        
        # Pfand return testing
        if users and products:
            pfand_history = api.get_pfand_history()
            if not pfand_history or len(pfand_history) == 0:
                print("⚠️ No pfand history found, cannot test return")
                return
            user_id, product_id = pfand_history[0]["user_id"], pfand_history[0]["product_id"]
            if pfand_history[0]["counter"] <= 0:
                print("⚠️ No pfand amount to return, cannot test return")
                return
            product_list = [{"id": product_id, "amount": 1}]
            self._test_function("submit_pfand_return", 
                              lambda: api.submit_pfand_return(user_id, product_list, 1), test_results)
    
    def _test_bank_functions(self, test_results):
        """Test bank-related functions"""
        print("\n🏦 Testing bank functions...")
        
        # Valid bank operations
        self._test_function("bank_withdraw", 
                          lambda: api.bank_withdraw(50.0, "Test withdrawal", 1), test_results)
        
        # Invalid bank operations
        self._test_function("bank_withdraw (invalid - no amount)", 
                          lambda: api.bank_withdraw(0, "Bad withdrawal", 1), test_results, expect_error=True)
    
    def _test_authentication_functions(self, test_results):
        """Test authentication functions"""
        print("\n🔐 Testing authentication functions...")
        
        # Test login with existing admin user
        self._test_function("login (valid admin)", 
                          lambda: api.login("admin", "password"), test_results)
        
        # Invalid login attempts
        self._test_function("login (invalid - wrong password)", 
                          lambda: api.login("admin_user", "wrong_password"), test_results, expect_error=True)
        self._test_function("login (invalid - non-existent user)", 
                          lambda: api.login("non_existent", "password"), test_results, expect_error=True)
        self._test_function("login (invalid - empty credentials)", 
                          lambda: api.login("", ""), test_results, expect_error=True)
        
        # Password change
        users = api.get_all_users()
        admin_user = next((u for u in users if u["name"] == "admin_user"), None)
        if admin_user:
            self._test_function("change_password (valid)", 
                              lambda: api.change_password(admin_user["user_id"], "admin123", "newpassword123"), test_results)
            
            # Invalid password changes
            self._test_function("change_password (invalid - wrong old password)", 
                              lambda: api.change_password(admin_user["user_id"], "wrong_old", "newpassword123"), test_results, expect_error=True)
    
    def _test_stock_history_functions(self, test_results):
        """Test stock history and stock management functions"""
        print("\n📊 Testing stock history functions...")
        
        # Get ingredients to test with
        print("  🔍 Fetching ingredients for stock history tests...")
        updated_all_history = api.get_all_stock_history()
        ingredients = api.get_all_ingredients()
        if not ingredients:
            print("  ⚠️ No ingredients found, skipping stock history tests")
            return
        
        # Test update_stock function
        test_ingredient = ingredients[0]
        ingredient_id = test_ingredient["ingredient_id"]
        original_stock = test_ingredient["stock_quantity"]
        
        # Test valid stock updates
        new_stock_amount = original_stock + 5
        self._test_function("update_stock (valid increase)", 
                          lambda: api.update_stock(ingredient_id, new_stock_amount, "Test stock increase"), test_results)
        
        # Test stock update with comment
        new_stock_amount_2 = new_stock_amount + 10
        self._test_function("update_stock (with comment)", 
                          lambda: api.update_stock(ingredient_id, new_stock_amount_2, "Test stock with detailed comment"), test_results)
        
        # Test stock decrease
        new_stock_amount_3 = new_stock_amount_2 - 3
        self._test_function("update_stock (decrease)", 
                          lambda: api.update_stock(ingredient_id, new_stock_amount_3, "Test stock decrease"), test_results)
        
        # Test invalid stock updates
        self._test_function("update_stock (invalid - negative stock)", 
                          lambda: api.update_stock(ingredient_id, -1, "Invalid negative stock"), test_results, expect_error=True)
        
        self._test_function("update_stock (invalid - invalid ingredient ID)", 
                          lambda: api.update_stock(99999, 10, "Invalid ingredient"), test_results, expect_error=True)
        
        self._test_function("update_stock (invalid - no ingredient ID)", 
                          lambda: api.update_stock(None, 10, "No ingredient ID"), test_results, expect_error=True)
        
        # Test get_stock_history function
        stock_history = self._test_function("get_stock_history (valid)", 
                          lambda: api.get_stock_history(ingredient_id), test_results)
        
        # Validate stock history structure
        if stock_history is not None:
            if isinstance(stock_history, list):
                test_results['passed'] += 1
                print(f"  ✅ get_stock_history: Returned list with {len(stock_history)} entries")
                
                # Validate individual stock history entries
                for i, entry in enumerate(stock_history):
                    if self._validate_stock_history_dict(entry, test_results):
                        print(f"  ✅ stock_history[{i}]: Structure validated")
                    else:
                        print(f"  ❌ stock_history[{i}]: Structure validation failed")
                        break
            else:
                test_results['failed'] += 1
                test_results['errors'].append(f"get_stock_history: Expected list, got {type(stock_history)}")
                print(f"  ❌ get_stock_history: Expected list, got {type(stock_history)}")
        
        # Test get_stock_history with invalid ingredient ID
        self._test_function("get_stock_history (invalid ingredient ID)", 
                          lambda: api.get_stock_history(99999), test_results, expect_error=False)
        
        self._test_function("get_stock_history (no ingredient ID)", 
                          lambda: api.get_stock_history(None), test_results, expect_error=True)
        
        # Test get_all_stock_history function
        all_stock_history = self._test_function("get_all_stock_history", 
                          lambda: api.get_all_stock_history(), test_results)
        
        # Validate all stock history structure
        if all_stock_history is not None:
            if isinstance(all_stock_history, list):
                test_results['passed'] += 1
                print(f"  ✅ get_all_stock_history: Returned list with {len(all_stock_history)} entries")
                
                # Validate sample entries
                for i, entry in enumerate(all_stock_history[:3]):  # Check first 3 entries
                    if self._validate_stock_history_dict(entry, test_results):
                        print(f"  ✅ all_stock_history[{i}]: Structure validated")
                    else:
                        print(f"  ❌ all_stock_history[{i}]: Structure validation failed")
                        break
            else:
                test_results['failed'] += 1
                test_results['errors'].append(f"get_all_stock_history: Expected list, got {type(all_stock_history)}")
                print(f"  ❌ get_all_stock_history: Expected list, got {type(all_stock_history)}")
        
        # Test edge cases
        print("  🔍 Testing stock history edge cases...")
        
        # Test stock update with empty comment
        self._test_function("update_stock (empty comment)", 
                          lambda: api.update_stock(ingredient_id, new_stock_amount_3 + 1, ""), test_results)
        
        # Test stock update with very long comment
        long_comment = "Very long comment " * 50  # 850+ characters
        self._test_function("update_stock (very long comment)", 
                          lambda: api.update_stock(ingredient_id, new_stock_amount_3 + 2, long_comment), test_results)
        
        # Test stock update with unicode characters
        unicode_comment = "Stock update with unicode: 测试 üöä €"
        self._test_function("update_stock (unicode comment)", 
                          lambda: api.update_stock(ingredient_id, new_stock_amount_3 + 3, unicode_comment), test_results)
        
        # Test multiple ingredients if available
        if len(ingredients) > 1:
            second_ingredient = ingredients[1]
            second_ingredient_id = second_ingredient["ingredient_id"]
            
            # Update stock for second ingredient
            self._test_function("update_stock (second ingredient)", 
                              lambda: api.update_stock(second_ingredient_id, second_ingredient["stock_quantity"] + 5, "Second ingredient test"), test_results)
            
            # Verify all_stock_history contains entries for both ingredients
            updated_all_history = api.get_all_stock_history()
            if updated_all_history:
                ingredient_ids_in_history = set(entry.get("ingredient_id") for entry in updated_all_history)
                if ingredient_id in ingredient_ids_in_history and second_ingredient_id in ingredient_ids_in_history:
                    test_results['passed'] += 1
                    print("  ✅ get_all_stock_history: Contains entries for multiple ingredients")
                else:
                    test_results['failed'] += 1
                    test_results['errors'].append("get_all_stock_history: Missing entries for tested ingredients")
                    print("  ❌ get_all_stock_history: Missing entries for tested ingredients")
        
        print("  📊 Stock history tests completed")
    
    def _validate_stock_history_dict(self, stock_history_dict, test_results):
        """Validate that a stock history dictionary has the expected fields"""
        expected_fields = ['history_id', 'ingredient_id', 'amount', 'comment', 'timestamp', 'ingredient_name']
        return self._validate_dict_structure(stock_history_dict, expected_fields, 'stock_history', test_results)
    
    def _test_soft_delete_functions(self, test_results):
        """Test soft delete and deletion management functions"""
        print("\n🗑️ Testing soft delete functions...")
        
        # First, get initial data to work with
        users = api.get_all_users()
        products = api.get_all_products()
        ingredients = api.get_all_ingredients()
        
        # Test dependency checking functions first
        if users:
            test_user = users[0]  # Use first user for testing
            self._test_function("check_dependencies (user)", 
                              lambda: api.check_deletion_dependencies("user", test_user["user_id"]), test_results)
        
        if products:
            test_product = products[0]  # Use first product for testing
            self._test_function("check_dependencies (product)", 
                              lambda: api.check_deletion_dependencies("product", test_product["product_id"]), test_results)
        
        if ingredients:
            test_ingredient = ingredients[0]  # Use first ingredient for testing
            self._test_function("check_dependencies (ingredient)", 
                              lambda: api.check_deletion_dependencies("ingredient", test_ingredient["ingredient_id"]), test_results)
        
        # Test soft delete functions (create test records first)
        print("  📝 Creating test records for soft delete...")
        
        # Create test user for soft delete
        try:
            test_user_result = api.add_user("test_soft_delete_user", 50.0, "user", 1)
            if test_user_result:
                test_user_id = test_user_result.get("user_id") if isinstance(test_user_result, dict) else test_user_result.user_id
                
                # Test soft delete user
                self._test_function("soft_delete_user", 
                                  lambda: api.soft_delete_user(test_user_id, "test_admin"), test_results)
                
                # Verify user is soft deleted (should not appear in get_all_users)
                users_after_delete = api.get_all_users()
                user_found = any(u["user_id"] == test_user_id for u in users_after_delete)
                if not user_found:
                    test_results['passed'] += 1
                    print(f"  ✅ soft_delete_user verification: User correctly filtered from get_all_users")
                else:
                    test_results['failed'] += 1
                    test_results['errors'].append("soft_delete_user verification: User still appears in get_all_users")
                    print(f"  ❌ soft_delete_user verification: User still appears in get_all_users")
                
                # Test restore user
                self._test_function("restore_user", 
                                  lambda: api.restore_user(test_user_id), test_results)
                
                # Verify user is restored (should appear in get_all_users again)
                users_after_restore = api.get_all_users()
                user_found_after_restore = any(u["user_id"] == test_user_id for u in users_after_restore)
                if user_found_after_restore:
                    test_results['passed'] += 1
                    print(f"  ✅ restore_user verification: User correctly restored to get_all_users")
                else:
                    test_results['failed'] += 1
                    test_results['errors'].append("restore_user verification: User not found after restore")
                    print(f"  ❌ restore_user verification: User not found after restore")
                
                # Test safe delete user (should do soft delete if no dependencies)
                self._test_function("safe_delete_user (soft)", 
                                  lambda: api.safe_delete_user(test_user_id, force=False), test_results)
        
        except Exception as e:
            print(f"  ⚠️ Could not create test user for soft delete: {e}")
        
        # Create test ingredient for soft delete
        try:
            test_ingredient_result = api.add_ingredient("test_soft_delete_ingredient", 2.0, 10, 5, 0.25)
            if test_ingredient_result:
                test_ingredient_id = test_ingredient_result.get("ingredient_id") if isinstance(test_ingredient_result, dict) else test_ingredient_result.ingredient_id
                
                # Test soft delete ingredient
                self._test_function("soft_delete_ingredient", 
                                  lambda: api.soft_delete_ingredient(test_ingredient_id, "test_admin"), test_results)
                
                # Verify ingredient is soft deleted
                ingredients_after_delete = api.get_all_ingredients()
                ingredient_found = any(i["ingredient_id"] == test_ingredient_id for i in ingredients_after_delete)
                if not ingredient_found:
                    test_results['passed'] += 1
                    print(f"  ✅ soft_delete_ingredient verification: Ingredient correctly filtered from get_all_ingredients")
                else:
                    test_results['failed'] += 1
                    test_results['errors'].append("soft_delete_ingredient verification: Ingredient still appears in get_all_ingredients")
                    print(f"  ❌ soft_delete_ingredient verification: Ingredient still appears in get_all_ingredients")
                
                # Test safe delete ingredient (should do soft delete if no dependencies)
                self._test_function("safe_delete_ingredient (soft)", 
                                  lambda: api.safe_delete_ingredient(test_ingredient_id, force=False), test_results)
        
        except Exception as e:
            print(f"  ⚠️ Could not create test ingredient for soft delete: {e}")
        
        # Create test product for soft delete (more complex due to ingredient dependencies)
        try:
            # First ensure we have at least one ingredient
            if ingredients:
                available_ingredient = ingredients[0]
                ingredient_id = available_ingredient["ingredient_id"]
                
                test_product_result = api.add_product("test_soft_delete_product", "test", 5.0, [ingredient_id], [1], 1)
                if test_product_result:
                    test_product_id = test_product_result.get("product_id") if isinstance(test_product_result, dict) else test_product_result.product_id
                    
                    # Test soft delete product
                    self._test_function("soft_delete_product", 
                                      lambda: api.soft_delete_product(test_product_id, "test_admin"), test_results)
                    
                    # Verify product is soft deleted
                    products_after_delete = api.get_all_products()
                    product_found = any(p["product_id"] == test_product_id for p in products_after_delete)
                    if not product_found:
                        test_results['passed'] += 1
                        print(f"  ✅ soft_delete_product verification: Product correctly filtered from get_all_products")
                    else:
                        test_results['failed'] += 1
                        test_results['errors'].append("soft_delete_product verification: Product still appears in get_all_products")
                        print(f"  ❌ soft_delete_product verification: Product still appears in get_all_products")
                    
                    # Test safe delete product (should do soft delete if no dependencies)
                    self._test_function("safe_delete_product (soft)", 
                                      lambda: api.safe_delete_product(test_product_id, force=False), test_results)
        
        except Exception as e:
            print(f"  ⚠️ Could not create test product for soft delete: {e}")
        
        # Test error cases
        print("  🔍 Testing soft delete error cases...")
        
        # Test soft delete with invalid IDs
        self._test_function("soft_delete_user (invalid ID)", 
                          lambda: api.soft_delete_user(99999, "test_admin"), test_results, expect_error=True)
        self._test_function("soft_delete_product (invalid ID)", 
                          lambda: api.soft_delete_product(99999, "test_admin"), test_results, expect_error=True)
        self._test_function("soft_delete_ingredient (invalid ID)", 
                          lambda: api.soft_delete_ingredient(99999, "test_admin"), test_results, expect_error=True)
        
        # Test check dependencies with invalid IDs
        self._test_function("check_dependencies (invalid entity type)", 
                          lambda: api.check_deletion_dependencies("invalid_type", 1), test_results, expect_error=True)
        
        # Test checking dependencies for non-existent IDs - these should succeed but indicate the entity doesn't exist
        result = self._test_function("check_dependencies (invalid user ID)", 
                          lambda: api.check_deletion_dependencies("user", 99999), test_results, expect_error=False)
        
        # Verify the result indicates the user doesn't exist
        if result and isinstance(result, dict):
            if not result.get('can_delete') and 'error' in result and 'does not exist' in result['error']:
                test_results['passed'] += 1
                print("  ✅ check_dependencies (invalid user ID) verification: Correctly detected non-existent user")
            else:
                test_results['failed'] += 1
                test_results['errors'].append("check_dependencies (invalid user ID): Should indicate user doesn't exist")
                print(f"  ❌ check_dependencies (invalid user ID): Expected error about non-existent user, got: {result}")
        
        self._test_function("check_dependencies (invalid product ID)", 
                          lambda: api.check_deletion_dependencies("product", 99999), test_results, expect_error=False)
        
        self._test_function("check_dependencies (invalid ingredient ID)", 
                          lambda: api.check_deletion_dependencies("ingredient", 99999), test_results, expect_error=False)
        
        # Test restore with invalid ID
        self._test_function("restore_user (invalid ID)", 
                          lambda: api.restore_user(99999), test_results, expect_error=True)
        
        print("  📊 Soft delete tests completed")

    def test_edge_cases(self):
        """Test specific edge cases and boundary conditions"""
        print("\n🔬 Testing edge cases...")
        
        edge_test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # Test with extreme values
        self._test_function("add_user (extreme balance)", 
                          lambda: api.add_user("extreme_user", 999999.99, "user", 1), edge_test_results)
        
        # Test with special characters
        self._test_function("add_ingredient (special chars)", 
                          lambda: api.add_ingredient("Spëcîäl_Ïngrédìent", 1.50, 10, 5, 0.0), edge_test_results)
        
        # Test with zero/negative values where appropriate
        self._test_function("add_ingredient (zero stock)", 
                          lambda: api.add_ingredient("Zero_Stock", 2.00, 0, 5, 0.0), edge_test_results)
        
        # Test concurrent operations simulation
        users = api.get_all_users()
        if users:
            user_id = users[0]["user_id"]
            # Multiple deposits in sequence
            for i in range(3):
                self._test_function(f"rapid_deposit_{i}", 
                                  lambda: api.deposit(user_id, 1.0, 1), edge_test_results)
        
        return edge_test_results
    
    def run_comprehensive_test_suite(self):
        """Run the complete test suite using generated test databases"""
        print("🚀 Starting Comprehensive API Test Suite")
        print("Using generated test databases for realistic testing scenarios")
        print("=" * 60)
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Prepare test database (select/generate and copy)
            self.prepare_test_database()
            
            print("\n" + "=" * 60)
            print("🧪 PHASE 1: Testing all API functions")
            print("=" * 60)
            
            # Test all functions
            main_results = self.test_all_api_functions()
            
            print("\n" + "=" * 60)
            print("🔬 PHASE 2: Testing edge cases")
            print("=" * 60)
            
            # Test edge cases
            edge_results = self.test_edge_cases()
            
            # Combined results
            total_passed = main_results['passed'] + edge_results['passed']
            total_failed = main_results['failed'] + edge_results['failed']
            total_tests = total_passed + total_failed
            
            print("\n" + "=" * 60)
            print("📊 FINAL RESULTS")
            print("=" * 60)
            print(f"🎯 Database used: {os.path.basename(self.current_db_path) if self.current_db_path else 'Unknown'}")
            print(f"📦 Version: {self.version or 'Latest available'}")
            print(f"📊 Database type: {self.database_type or 'Auto-selected'}")
            print(f"✅ Total Passed: {total_passed}")
            print(f"❌ Total Failed: {total_failed}")
            print(f"📈 Success Rate: {(total_passed/total_tests*100):.1f}%")
            
            if main_results['errors'] or edge_results['errors']:
                print("\n🚨 Error Details:")
                for error in main_results['errors'] + edge_results['errors']:
                    print(f"  • {error}")
            
            print(f"\n💾 Test database preserved at: {self.current_db_path}")
            print("   You can examine this database to see all test data and results")
            
            return total_failed == 0  # Return True if all tests passed
            
        except Exception as e:
            print(f"\n💥 Test suite failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Don't clean up automatically - let user examine the database
            print("\n💡 Test environment preserved for examination")
            print(f"   Database: {self.current_db_path}")
            if self.temp_dir:
                print(f"   To clean up: rm -rf {self.temp_dir}")

def list_available_databases():
    """List all available test databases"""
    tester = ComprehensiveAPITester()
    
    if not tester.discover_available_databases():
        print("❌ No test databases found")
        print(f"💡 Expected location: {tester.test_databases_dir}/")
        print("💡 To generate test databases:")
        print("   python testing/generate_test_databases.py all --version v1.0")
        return
    
    print("📋 Available Test Databases:")
    print("=" * 40)
    
    for version in tester.available_versions:
        print(f"\n📦 Version: {version}")
        databases = tester.available_databases[version]
        for db_type, db_path in databases.items():
            db_name = os.path.basename(db_path)
            print(f"  • {db_type}: {db_name}")
    
    latest = tester.get_latest_version()
    if latest:
        print(f"\n🎯 Latest version: {latest}")

def _inspect_single_database(db_path, db_type, detailed=False):
    """Inspect a single database file and show table contents"""
    print(f"\n📊 Database: {db_type} ({os.path.basename(db_path)})")
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("  ⚠️ No tables found")
            conn.close()
            return
        
        # Show table info
        for table in tables:
            _inspect_single_table(cursor, table, detailed)
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ Error opening database: {e}")

def _inspect_single_table(cursor, table, detailed=False):
    """Inspect a single table and show its contents"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        if detailed and count > 0:
            # Get column info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"  📋 {table}: {count} records")
            print(f"     Columns: {', '.join(column_names)}")
            
            # Show sample data for small tables
            if count <= 5:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                sample_rows = cursor.fetchall()
                if sample_rows:
                    print("     Sample data:")
                    for i, row in enumerate(sample_rows):
                        print(f"       Row {i+1}: {dict(zip(column_names, row))}")
        else:
            print(f"  📋 {table}: {count} records")
            
    except Exception as e:
        print(f"  ❌ {table}: Error reading table ({e})")

def inspect_databases(version=None, detailed=False):
    """Inspect all database files and show their table contents"""
    tester = ComprehensiveAPITester()
    
    if not tester.discover_available_databases():
        print(NO_DATABASES_MSG)
        print(f"💡 Expected location: {tester.test_databases_dir}/")
        return
    
    versions_to_inspect = [version] if version and version in tester.available_versions else tester.available_versions
    
    if version and version not in tester.available_versions:
        print(f"❌ Version '{version}' not found")
        print(f"📋 Available versions: {', '.join(tester.available_versions)}")
        return
    
    print("🔍 Database Table Inspection")
    print("=" * 60)
    
    for version_name in versions_to_inspect:
        print(f"\n📦 Version: {version_name}")
        print("-" * 40)
        
        databases = tester.available_databases[version_name]
        
        for db_type, db_path in databases.items():
            _inspect_single_database(db_path, db_type, detailed)
    
    print("\n💡 Tip: Use --inspect-detailed for column info and sample data")

# CLI runner
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comprehensive Admin API Test Suite")
    parser.add_argument(
        "--version",
        type=str,
        help="Test database version to use (e.g., v1.0, baseline). If not specified, uses latest available."
    )
    parser.add_argument(
        "--database-type",
        type=str,
        choices=["minimal", "comprehensive", "edge", "performance"],
        help="Type of test database to use. If not specified, auto-selects best available."
    )
    parser.add_argument(
        "--list-databases",
        action="store_true",
        help="List all available test databases and exit"
    )
    parser.add_argument(
        "--inspect",
        type=str,
        nargs="?",
        const="all",
        help="Inspect database tables. Specify version (e.g., v1.0) or 'all' for all versions"
    )
    parser.add_argument(
        "--inspect-detailed",
        action="store_true",
        help="Show detailed table info including columns and sample data when inspecting"
    )
    parser.add_argument(
        "--inspect-databases",
        action="store_true",
        help="Inspect database files and show table contents"
    )
    
    args = parser.parse_args()
    
    if args.list_databases:
        list_available_databases()
        exit(0)
    
    if args.inspect:
        version_to_inspect = None if args.inspect == "all" else args.inspect
        inspect_databases(version=version_to_inspect, detailed=args.inspect_detailed)
        exit(0)
    
    if args.inspect_databases:
        inspect_databases(args.version, args.inspect_detailed)
        exit(0)
    
    print("🧪 Comprehensive Admin API Test Suite")
    print("Testing all admin_api.py functions using generated test databases")
    
    if args.version:
        print(f"🎯 Requested version: {args.version}")
    if args.database_type:
        print(f"📊 Requested database type: {args.database_type}")
    
    print()
    
    tester = ComprehensiveAPITester(version=args.version, database_type=args.database_type)
    success = tester.run_comprehensive_test_suite()
    
    if success:
        print("\n🎉 All tests passed! Your API is working correctly.")
        exit(0)
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        exit(1)
