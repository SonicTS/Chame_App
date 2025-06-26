# comprehensive_api_tests.py
# Complete testing framework for admin_api functions with database setup

import os
import sys
import tempfile
import shutil
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your modules
import services.admin_api as api

logger = logging.getLogger(__name__)

class ComprehensiveAPITester:
    """Complete testing framework for all admin API functions"""
    
    def __init__(self, test_db_path=None):
        self.test_db_path = test_db_path or "test_database.db"
        self.temp_dir = None
        self.created_entities = {
            'users': [],
            'ingredients': [],
            'products': [],
            'sales': [],
            'toast_rounds': []
        }
        
    def setup_test_environment(self):
        """Set up temporary directory and database for testing"""
        self.temp_dir = tempfile.mkdtemp(prefix="api_test_")
        self.test_db_path = os.path.join(self.temp_dir, "test_api.db")
        
        # Set environment variable to use test database
        os.environ["PRIVATE_STORAGE"] = self.temp_dir
        
        print(f"📁 Test environment created at: {self.temp_dir}")
        print(f"🗄️ Test database: {self.test_db_path}")
        
    def teardown_test_environment(self):
        """Clean up test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up test environment: {self.temp_dir}")
    
    def create_test_database(self):
        """Initialize database and create basic structure"""
        print("🔧 Creating test database...")
        
        # Reset the global database instance
        api.database = None
        
        # Create new database instance
        db = api.create_database()
        
        print("✅ Test database created successfully")
        return db
    
    def populate_generic_test_data(self):
        """Create a comprehensive set of test data"""
        print("📊 Populating database with generic test data...")
        
        # Create test users
        self._create_test_users()
        
        # Create test ingredients
        self._create_test_ingredients()
        
        # Create test products
        self._create_test_products()
        
        # Create test sales
        self._create_test_sales()
        
        # Create test toast rounds
        self._create_test_toast_rounds()
        
        print("✅ Generic test data populated successfully")
    
    def _create_test_users(self):
        """Create various types of test users"""
        print("👥 Creating test users...")
        
        users_data = [
            ("admin_user", 1000.0, "admin", "admin123"),
            ("wirt_user", 500.0, "wirt", "wirt1234"),
            ("regular_user1", 50.0, "user", ""),
            ("regular_user2", 25.75, "user", ""),
            ("broke_user", 0.0, "user", ""),
            ("rich_user", 999.99, "user", ""),
            ("test_müller", 100.0, "user", ""),  # Test special characters
            ("user_with_debt", -10.0, "user", ""),  # Test negative balance
        ]
        
        for name, balance, role, password in users_data:
            try:
                user = api.add_user(name, balance, role, password)
                self.created_entities['users'].append(user)
                print(f"  ✅ Created {role}: {name} (balance: {balance})")
            except Exception as e:
                print(f"  ❌ Failed to create user {name}: {e}")
    
    def _create_test_ingredients(self):
        """Create various test ingredients"""
        print("🥬 Creating test ingredients...")
        
        ingredients_data = [
            ("Bread", 2.50, 20, 10, 0.0),  # Basic ingredient
            ("Cheese", 4.00, 15, 8, 0.0),
            ("Ham", 5.50, 10, 6, 0.0),
            ("Tomato", 3.00, 25, 12, 0.0),
            ("Lettuce", 2.00, 30, 15, 0.0),
            ("Cola", 1.50, 24, 1, 0.25),  # With Pfand
            ("Beer", 2.00, 20, 1, 0.08),  # With Pfand
            ("Water", 1.00, 50, 1, 0.25),  # With Pfand
            ("Expensive_Ingredient", 99.99, 1, 1, 0.0),  # Edge case: expensive
            ("Free_Sample", 0.01, 100, 50, 0.0),  # Edge case: very cheap
        ]
        
        for name, price, stock, number, pfand in ingredients_data:
            try:
                ingredient = api.add_ingredient(name, price, stock, number, pfand)
                self.created_entities['ingredients'].append(ingredient)
                print(f"  ✅ Created ingredient: {name} (stock: {stock}, pfand: {pfand})")
            except Exception as e:
                print(f"  ❌ Failed to create ingredient {name}: {e}")
    
    def _create_test_products(self):
        """Create various test products"""
        print("🍞 Creating test products...")
        
        # Get created ingredients for product creation
        ingredients = api.get_all_ingredients()
        if not ingredients or len(ingredients) < 3:
            print("  ⚠️ Not enough ingredients to create products")
            return
        
        products_data = [
            {
                "name": "Classic Toast",
                "category": "toast",
                "price": 3.50,
                "ingredient_indices": [0, 1],  # Bread, Cheese
                "quantities": [1, 1],
                "toaster_space": 1
            },
            {
                "name": "Ham & Cheese Toast",
                "category": "toast",
                "price": 5.00,
                "ingredient_indices": [0, 1, 2],  # Bread, Cheese, Ham
                "quantities": [1, 1, 1],
                "toaster_space": 1
            },
            {
                "name": "Veggie Toast",
                "category": "toast",
                "price": 4.00,
                "ingredient_indices": [0, 3, 4],  # Bread, Tomato, Lettuce
                "quantities": [1, 2, 2],
                "toaster_space": 1
            },
            {
                "name": "Cola",
                "category": "drink",
                "price": 2.00,
                "ingredient_indices": [5],  # Cola
                "quantities": [1],
                "toaster_space": 0
            },
            {
                "name": "Premium Sandwich",
                "category": "sandwich",
                "price": 15.99,
                "ingredient_indices": [0, 1, 2, 3, 4],  # All main ingredients
                "quantities": [2, 2, 2, 1, 1],
                "toaster_space": 2
            }
        ]
        
        for product_data in products_data:
            try:
                # Get ingredient IDs
                ingredient_ids = []
                for idx in product_data["ingredient_indices"]:
                    if idx < len(ingredients):
                        ingredient_ids.append(ingredients[idx]["ingredient_id"])
                
                product = api.add_product(
                    product_data["name"],
                    product_data["category"],
                    product_data["price"],
                    ingredient_ids,
                    product_data["quantities"],
                    product_data["toaster_space"]
                )
                self.created_entities['products'].append(product)
                print(f"  ✅ Created product: {product_data['name']} (price: {product_data['price']})")
            except Exception as e:
                print(f"  ❌ Failed to create product {product_data['name']}: {e}")
    
    def _create_test_sales(self):
        """Create various test sales"""
        print("💰 Creating test sales...")
        
        users = api.get_all_users()
        products = api.get_all_products()
        
        if not users or not products:
            print("  ⚠️ No users or products available for sales")
            return
        
        # Create various sales scenarios
        sales_scenarios = [
            # (user_index, product_index, quantity)
            (0, 0, 1),  # Admin buys classic toast
            (2, 1, 2),  # Regular user buys 2 ham & cheese toasts
            (3, 3, 1),  # Regular user buys cola
            (1, 4, 1),  # Wirt buys premium sandwich
            (5, 0, 3),  # Rich user buys 3 classic toasts
        ]
        
        for user_idx, product_idx, quantity in sales_scenarios:
            try:
                if user_idx < len(users) and product_idx < len(products):
                    sale = api.make_purchase(
                        users[user_idx]["user_id"],
                        products[product_idx]["product_id"],
                        quantity
                    )
                    self.created_entities['sales'].append(sale)
                    print(f"  ✅ Sale: {users[user_idx]['name']} bought {quantity}x {products[product_idx]['name']}")
            except Exception as e:
                print(f"  ❌ Failed to create sale: {e}")
    
    def _create_test_toast_rounds(self):
        """Create test toast rounds"""
        print("🍞 Creating test toast rounds...")
        
        users = api.get_all_users()
        products = api.get_all_products()
        
        if not users or not products:
            print("  ⚠️ No users or products available for toast rounds")
            return
        
        # Filter for toast products
        toast_products = [p for p in products if p.get("category") == "toast"]
        
        if len(toast_products) < 2 or len(users) < 3:
            print("  ⚠️ Not enough toast products or users for toast rounds")
            return
        
        try:
            # Create a toast round with multiple products and users
            product_ids = [toast_products[0]["product_id"], toast_products[1]["product_id"]]
            user_selections = [users[0]["user_id"], users[2]["user_id"]]
            
            toast_round = api.add_toast_round(product_ids, user_selections)
            self.created_entities['toast_rounds'].append(toast_round)
            print(f"  ✅ Created toast round with {len(product_ids)} products")
        except Exception as e:
            print(f"  ❌ Failed to create toast round: {e}")
    
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
        """Test all data fetching functions"""
        print("\n📊 Testing data fetcher functions...")
        
        # Basic data fetchers
        self._test_function("get_all_users", lambda: api.get_all_users(), test_results)
        self._test_function("get_all_products", lambda: api.get_all_products(), test_results)
        self._test_function("get_all_ingredients", lambda: api.get_all_ingredients(), test_results)
        self._test_function("get_all_sales", lambda: api.get_all_sales(), test_results)
        self._test_function("get_all_toast_products", lambda: api.get_all_toast_products(), test_results)
        self._test_function("get_all_toast_rounds", lambda: api.get_all_toast_rounds(), test_results)
        self._test_function("get_bank", lambda: api.get_bank(), test_results)
        self._test_function("get_bank_transaction", lambda: api.get_bank_transaction(), test_results)
        self._test_function("get_pfand_history", lambda: api.get_pfand_history(), test_results)
        
        # Filtered transactions
        self._test_function("get_filtered_transaction (all)", 
                          lambda: api.get_filtered_transaction(), test_results)
        self._test_function("get_filtered_transaction (user 1)", 
                          lambda: api.get_filtered_transaction(user_id=1), test_results)
        self._test_function("get_filtered_transaction (sales only)", 
                          lambda: api.get_filtered_transaction(tx_type="sale"), test_results)
    
    def _test_user_management(self, test_results):
        """Test user management functions"""
        print("\n👥 Testing user management functions...")
        
        # Valid user creation
        self._test_function("add_user (valid regular)", 
                          lambda: api.add_user("test_user_new", 20.0, "user"), test_results)
        self._test_function("add_user (valid admin)", 
                          lambda: api.add_user("test_admin_new", 100.0, "admin", "password123"), test_results)
        
        # Invalid user creation (should fail)
        self._test_function("add_user (invalid - no name)", 
                          lambda: api.add_user("", 20.0, "user"), test_results, expect_error=True)
        self._test_function("add_user (invalid - admin no password)", 
                          lambda: api.add_user("bad_admin", 100.0, "admin", ""), test_results, expect_error=True)
        self._test_function("add_user (invalid - short admin password)", 
                          lambda: api.add_user("bad_admin2", 100.0, "admin", "123"), test_results, expect_error=True)
        
        # Money operations
        users = api.get_all_users()
        if users:
            user_id = users[0]["user_id"]
            self._test_function("deposit", 
                              lambda: api.deposit(user_id, 10.0), test_results)
            self._test_function("withdraw", 
                              lambda: api.withdraw(user_id, 5.0), test_results)
            
            # Invalid money operations
            self._test_function("withdraw (insufficient funds)", 
                              lambda: api.withdraw(user_id, 99999.0), test_results, expect_error=True)
            self._test_function("deposit (invalid amount)", 
                              lambda: api.deposit(user_id, -10.0), test_results, expect_error=True)
    
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
            restock_list = [{ingredient_id: 5}]
            self._test_function("restock_ingredients", 
                              lambda: api.restock_ingredients(restock_list), test_results)
    
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
        
        if users and products:
            user_id = users[0]["user_id"]
            product_id = products[0]["product_id"]
            
            # Valid purchase
            self._test_function("make_purchase (valid)", 
                              lambda: api.make_purchase(user_id, product_id, 1), test_results)
            
            # Invalid purchases
            self._test_function("make_purchase (invalid - no user)", 
                              lambda: api.make_purchase(0, product_id, 1), test_results, expect_error=True)
            self._test_function("make_purchase (invalid - no product)", 
                              lambda: api.make_purchase(user_id, 0, 1), test_results, expect_error=True)
            self._test_function("make_purchase (invalid - zero quantity)", 
                              lambda: api.make_purchase(user_id, product_id, 0), test_results, expect_error=True)
        
        # Pfand return testing
        if users and products:
            product_list = [{"product_id": products[0]["product_id"], "quantity": 1}]
            self._test_function("submit_pfand_return", 
                              lambda: api.submit_pfand_return(users[0]["user_id"], product_list), test_results)
    
    def _test_bank_functions(self, test_results):
        """Test bank-related functions"""
        print("\n🏦 Testing bank functions...")
        
        # Valid bank operations
        self._test_function("bank_withdraw", 
                          lambda: api.bank_withdraw(50.0, "Test withdrawal"), test_results)
        
        # Invalid bank operations
        self._test_function("bank_withdraw (invalid - no amount)", 
                          lambda: api.bank_withdraw(0, "Bad withdrawal"), test_results, expect_error=True)
    
    def _test_authentication_functions(self, test_results):
        """Test authentication functions"""
        print("\n🔐 Testing authentication functions...")
        
        # Test login with existing admin user
        self._test_function("login (valid admin)", 
                          lambda: api.login("admin_user", "admin123"), test_results)
        
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
                          lambda: api.add_user("extreme_user", 999999.99, "user"), edge_test_results)
        
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
                                  lambda: api.deposit(user_id, 1.0), edge_test_results)
        
        return edge_test_results
    
    def run_comprehensive_test_suite(self):
        """Run the complete test suite"""
        print("🚀 Starting Comprehensive API Test Suite")
        print("=" * 60)
        
        try:
            # Setup
            self.setup_test_environment()
            self.create_test_database()
            
            # Populate with test data
            self.populate_generic_test_data()
            
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
            print(f"✅ Total Passed: {total_passed}")
            print(f"❌ Total Failed: {total_failed}")
            print(f"📈 Success Rate: {(total_passed/total_tests*100):.1f}%")
            
            if main_results['errors'] or edge_results['errors']:
                print("\n🚨 Error Details:")
                for error in main_results['errors'] + edge_results['errors']:
                    print(f"  • {error}")
            
            print(f"\n💾 Test database saved at: {self.test_db_path}")
            print("   You can examine this database to see all created test data")
            
            return total_failed == 0  # Return True if all tests passed
            
        except Exception as e:
            print(f"\n💥 Test suite failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Don't clean up automatically - let user examine the database
            print(f"\n💡 Test environment preserved for examination")
            print(f"   Database: {self.test_db_path}")
            print(f"   To clean up: rm -rf {self.temp_dir}")

# CLI runner
if __name__ == "__main__":
    print("🧪 Comprehensive Admin API Test Suite")
    print("This will test every function in admin_api.py with realistic data")
    print()
    
    tester = ComprehensiveAPITester()
    success = tester.run_comprehensive_test_suite()
    
    if success:
        print("\n🎉 All tests passed! Your API is working correctly.")
        exit(0)
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        exit(1)
