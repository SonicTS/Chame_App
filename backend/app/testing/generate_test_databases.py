#!/usr/bin/env python3
"""
Database Generator for Testing
Creates different types of test databases for manual and automated testing
"""

import os
import sys
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import services.admin_api as api

class TestDatabaseGenerator:
    """Generate test databases with different scenarios"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or "test_databases"
        self.current_db_path = None
        
    def create_minimal_database(self, db_name: str = "minimal_test.db") -> str:
        """Create a minimal database with just basic entities"""
        db_path = self._setup_database(db_name)
        
        print("🔧 Creating minimal test database...")
        
        # Create basic users
        api.add_user("admin", 100.0, "admin", "admin123")
        api.add_user("testuser", 50.0, "user")
        
        # Create basic ingredients
        api.add_ingredient("Bread", 2.50, 10, 8, 0.0)
        api.add_ingredient("Cheese", 3.00, 15, 6, 0.0)
        
        # Create basic product
        ingredients = api.get_all_ingredients()
        if len(ingredients) >= 2:
            api.add_product("Toast", "toast", 4.00, 
                          [ingredients[0]["ingredient_id"], ingredients[1]["ingredient_id"]], 
                          [1, 1], 1)
        
        print(f"✅ Minimal database created: {db_path}")
        return db_path
    
    def create_comprehensive_database(self, db_name: str = "comprehensive_test.db") -> str:
        """Create a comprehensive database with realistic data"""
        db_path = self._setup_database(db_name)
        
        print("🔧 Creating comprehensive test database...")
        
        # Users with different roles and balances
        users_data = [
            ("admin_user", 1000.0, "admin", "admin123"),
            ("manager_user", 500.0, "wirt", "wirt1234"),
            ("customer1", 25.50, "user", ""),
            ("customer2", 100.0, "user", ""),
            ("broke_customer", 0.0, "user", ""),
            ("vip_customer", 500.0, "user", ""),
        ]
        
        for name, balance, role, password in users_data:
            try:
                api.add_user(name, balance, role, password)
                print(f"  ✅ Created user: {name} ({role})")
            except Exception as e:
                print(f"  ⚠️ Failed to create user {name}: {e}")
        
        # Comprehensive ingredients
        ingredients_data = [
            ("Bread", 2.50, 20, 10, 0.0),
            ("Cheese", 4.00, 15, 8, 0.0),
            ("Ham", 6.00, 10, 6, 0.0),
            ("Tomato", 3.00, 25, 12, 0.0),
            ("Lettuce", 2.00, 30, 15, 0.0),
            ("Cola", 1.50, 24, 1, 0.25),  # With Pfand
            ("Beer", 2.00, 20, 1, 0.08),
            ("Water", 1.00, 50, 1, 0.25),
            ("Butter", 3.50, 8, 12, 0.0),
            ("Mustard", 2.50, 5, 20, 0.0),
        ]
        
        for name, price, stock, number, pfand in ingredients_data:
            try:
                api.add_ingredient(name, price, stock, number, pfand)
                print(f"  ✅ Created ingredient: {name}")
            except Exception as e:
                print(f"  ⚠️ Failed to create ingredient {name}: {e}")
        
        # Various products
        ingredients = api.get_all_ingredients()
        if len(ingredients) >= 5:
            products_data = [
                ("Classic Toast", "toast", 3.50, [0, 1], [1, 1], 1),
                ("Ham & Cheese Toast", "toast", 5.00, [0, 1, 2], [1, 1, 1], 1),
                ("Veggie Toast", "toast", 4.00, [0, 3, 4], [1, 2, 2], 1),
                ("Cola Bottle", "drink", 2.00, [5], [1], 0),
                ("Beer Bottle", "drink", 2.50, [6], [1], 0),
                ("Premium Sandwich", "sandwich", 8.99, [0, 1, 2, 8, 9], [2, 2, 2, 1, 1], 2),
            ]
            
            for name, category, price, ingredient_indices, quantities, toaster_space in products_data:
                ingredient_ids = [ingredients[i]["ingredient_id"] for i in ingredient_indices]
                api.add_product(name, category, price, ingredient_ids, quantities, toaster_space)
        
        # Create some sales
        users = api.get_all_users()
        products = api.get_all_products()
        if users and products:
            # Some realistic purchases - be careful with user indices and balances
            try:
                api.make_purchase(users[2]["user_id"], products[0]["product_id"], 1)  # customer1 buys toast
                api.make_purchase(users[3]["user_id"], products[3]["product_id"], 2)  # customer2 buys cola
                api.make_purchase(users[0]["user_id"], products[5]["product_id"], 1)  # admin buys premium sandwich
            except Exception as e:
                print(f"⚠️ Note: Some sales creation failed: {e}")
        
        print(f"✅ Comprehensive database created: {db_path}")
        return db_path
    
    def create_edge_case_database(self, db_name: str = "edge_case_test.db") -> str:
        """Create a database with edge cases for testing"""
        db_path = self._setup_database(db_name)
        
        print("🔧 Creating edge case test database...")
        
        # Edge case users
        edge_users = [
            ("normal_admin", 100.0, "admin", "password123"),
            ("unicode_user_测试", 50.0, "user", ""),
            ("negative_balance", -25.0, "user", ""),
            ("zero_balance", 0.0, "user", ""),
            ("max_balance", 99999.99, "user", ""),
            ("special_chars_üöä", 30.0, "user", ""),
        ]
        
        for name, balance, role, password in edge_users:
            api.add_user(name, balance, role, password)
        
        # Edge case ingredients
        edge_ingredients = [
            ("Very_Expensive_Item", 99.99, 1, 1, 0.0),
            ("Very_Cheap_Item", 0.01, 100, 1000, 0.0),
            ("High_Pfand_Item", 2.00, 10, 1, 5.00),
            ("Zero_Stock_Item", 5.00, 0, 10, 0.0),
            ("Unicode_Ingredient_测试", 3.00, 15, 8, 0.25),
            ("Special_Chars_üöä", 2.50, 20, 12, 0.0),
        ]
        
        for name, price, stock, number, pfand in edge_ingredients:
            api.add_ingredient(name, price, stock, number, pfand)
        
        print(f"✅ Edge case database created: {db_path}")
        return db_path
    
    def create_performance_database(self, db_name: str = "performance_test.db") -> str:
        """Create a database with many entities for performance testing"""
        db_path = self._setup_database(db_name)
        
        print("🔧 Creating performance test database...")
        
        # Create many users
        for i in range(50):
            api.add_user(f"user_{i:03d}", float(i * 10), "user")
        
        # Admin users
        api.add_user("admin", 1000.0, "admin", "admin123")
        api.add_user("manager", 500.0, "wirt", "manager123")
        
        # Many ingredients
        ingredient_names = [
            "Bread", "Cheese", "Ham", "Tomato", "Lettuce", "Onion", "Pickle", 
            "Mustard", "Mayo", "Ketchup", "Butter", "Salami", "Turkey", "Bacon",
            "Cola", "Beer", "Water", "Juice", "Coffee", "Tea"
        ]
        
        for i, name in enumerate(ingredient_names):
            pfand = 0.25 if name in ["Cola", "Beer", "Water", "Juice"] else 0.0
            api.add_ingredient(f"{name}_{i}", 2.0 + i * 0.5, 20 + i, 8 + i % 5, pfand)
        
        print(f"✅ Performance database created: {db_path}")
        return db_path
    
    def _setup_database(self, db_name: str) -> str:
        """Setup database environment and return path"""
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up temporary environment
        temp_dir = tempfile.mkdtemp(prefix="dbgen_")
        os.environ["PRIVATE_STORAGE"] = temp_dir
        
        # Force reset database instance completely
        api.database = None
        
        # Remove any existing database file in the temp directory
        temp_db_path = os.path.join(temp_dir, "kassensystem.db")
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        
        # Create fresh database - force creation by setting database to None first
        api.database = None  # Ensure it's None
        api.create_database()
        
        # Verify the database is fresh by checking if it has any users
        try:
            users = api.get_all_users()
            if users:
                print(f"⚠️ Warning: Database not fresh, found {len(users)} existing users")
                # Force recreate the database instance
                from chame_app.database import Database
                api.database = Database()
        except Exception:
            # This is expected for a fresh database
            pass
        
        # Final database path
        final_path = os.path.join(self.output_dir, db_name)
        self.current_db_path = temp_db_path
        
        return final_path
    
    def finalize_database(self, final_path: str):
        """Copy database to final location and cleanup"""
        if self.current_db_path and os.path.exists(self.current_db_path):
            shutil.copy2(self.current_db_path, final_path)
            print(f"💾 Database saved to: {final_path}")
            # Clean up temp directory - try to close any open connections first
            try:
                import time
                time.sleep(0.1)  # Brief pause to allow file handles to close
                temp_dir = os.path.dirname(self.current_db_path)
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"⚠️ Note: Temp directory cleanup failed (file may be in use): {e}")
                print(f"   Temp dir: {os.path.dirname(self.current_db_path)}")
        
    def generate_all_databases(self):
        """Generate all types of test databases"""
        print("🚀 Generating all test databases...")
        print("=" * 50)
        
        databases = [
            ("minimal", self.create_minimal_database),
            ("comprehensive", self.create_comprehensive_database),
            ("edge_case", self.create_edge_case_database),
            ("performance", self.create_performance_database),
        ]
        
        created_dbs = []
        for db_type, create_func in databases:
            try:
                db_path = create_func(f"{db_type}_test.db")
                self.finalize_database(db_path)
                created_dbs.append(db_path)
            except Exception as e:
                print(f"❌ Failed to create {db_type} database: {e}")
        
        print("\n" + "=" * 50)
        print("📊 GENERATION SUMMARY")
        print("=" * 50)
        print(f"✅ Created {len(created_dbs)} test databases:")
        for db_path in created_dbs:
            print(f"  • {db_path}")
        
        print(f"\n📁 All databases in: {os.path.abspath(self.output_dir)}")
        print("\n💡 Usage:")
        print("  • Copy any database to 'kassensystem.db' to use as active database")
        print("  • Use these databases to test different scenarios")
        print("  • Import into SQLite browser for manual inspection")

# CLI interface
if __name__ == "__main__":
    import sys
    
    generator = TestDatabaseGenerator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "minimal":
            db_path = generator.create_minimal_database()
            generator.finalize_database(db_path)
        elif command == "comprehensive":
            db_path = generator.create_comprehensive_database()
            generator.finalize_database(db_path)
        elif command == "edge":
            db_path = generator.create_edge_case_database()
            generator.finalize_database(db_path)
        elif command == "performance":
            db_path = generator.create_performance_database()
            generator.finalize_database(db_path)
        elif command == "all":
            generator.generate_all_databases()
        else:
            print("Usage: python generate_test_databases.py [minimal|comprehensive|edge|performance|all]")
    else:
        generator.generate_all_databases()
