# deletion_service.py
# Safe deletion service with referential integrity checks

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DeletionService:
    """Service to handle safe deletion of database records"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def soft_delete_user(self, user_id: int, deleted_by_user: str = None) -> Dict[str, Any]:
        """Perform soft delete on a user"""
        result = {'success': False, 'message': '', 'details': {}}
        
        try:
            from models.user_table import User
            
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if not user:
                result['message'] = 'User not found'
                return result
            
            if user.is_deleted:
                result['message'] = 'User is already deleted'
                return result
            
            # Perform soft delete
            user.soft_delete(deleted_by_user)
            self.db.commit()
            
            result['success'] = True
            result['message'] = f'User "{user.name}" soft deleted successfully'
            result['details'] = {'deleted_at': user.deleted_at, 'deleted_by': user.deleted_by}
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error soft deleting user {user_id}: {e}")
            result['message'] = f'Error soft deleting user: {str(e)}'
        
        return result
    
    def soft_delete_product(self, product_id: int, deleted_by_user: str = None) -> Dict[str, Any]:
        """Perform soft delete on a product"""
        result = {'success': False, 'message': '', 'details': {}}
        
        try:
            from models.product_table import Product
            
            product = self.db.query(Product).filter(Product.product_id == product_id).first()
            if not product:
                result['message'] = 'Product not found'
                return result
            
            if product.is_deleted:
                result['message'] = 'Product is already deleted'
                return result
            
            # Perform soft delete
            product.soft_delete(deleted_by_user)
            self.db.commit()
            
            result['success'] = True
            result['message'] = f'Product "{product.name}" soft deleted successfully'
            result['details'] = {'deleted_at': product.deleted_at, 'deleted_by': product.deleted_by}
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error soft deleting product {product_id}: {e}")
            result['message'] = f'Error soft deleting product: {str(e)}'
        
        return result
    
    def soft_delete_ingredient(self, ingredient_id: int, deleted_by_user: str = None) -> Dict[str, Any]:
        """Perform soft delete on an ingredient"""
        result = {'success': False, 'message': '', 'details': {}}
        
        try:
            from models.ingredient import Ingredient
            
            ingredient = self.db.query(Ingredient).filter(Ingredient.ingredient_id == ingredient_id).first()
            if not ingredient:
                result['message'] = 'Ingredient not found'
                return result
            
            if ingredient.is_deleted:
                result['message'] = 'Ingredient is already deleted'
                return result
            
            # Perform soft delete
            ingredient.soft_delete(deleted_by_user)
            self.db.commit()
            
            result['success'] = True
            result['message'] = f'Ingredient "{ingredient.name}" soft deleted successfully'
            result['details'] = {'deleted_at': ingredient.deleted_at, 'deleted_by': ingredient.deleted_by}
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error soft deleting ingredient {ingredient_id}: {e}")
            result['message'] = f'Error soft deleting ingredient: {str(e)}'
        
        return result
    
    def restore_user(self, user_id: int) -> Dict[str, Any]:
        """Restore a soft-deleted user"""
        result = {'success': False, 'message': ''}
        
        try:
            from models.user_table import User
            
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if not user:
                result['message'] = 'User not found'
                return result
            
            if not user.is_deleted:
                result['message'] = 'User is not deleted'
                return result
            
            user.restore()
            self.db.commit()
            
            result['success'] = True
            result['message'] = f'User "{user.name}" restored successfully'
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error restoring user {user_id}: {e}")
            result['message'] = f'Error restoring user: {str(e)}'
        
        return result
    
    def restore_product(self, product_id: int) -> Dict[str, Any]:
        """Restore a soft-deleted product"""
        result = {'success': False, 'message': ''}
        
        try:
            from models.product_table import Product
            
            product = self.db.query(Product).filter(Product.product_id == product_id).first()
            if not product:
                result['message'] = 'Product not found'
                return result
            
            if not product.is_deleted:
                result['message'] = 'Product is not deleted'
                return result
            
            product.restore()
            self.db.commit()
            
            result['success'] = True
            result['message'] = f'Product "{product.name}" restored successfully'
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error restoring product {product_id}: {e}")
            result['message'] = f'Error restoring product: {str(e)}'
        
        return result
    
    def restore_ingredient(self, ingredient_id: int) -> Dict[str, Any]:
        """Restore a soft-deleted ingredient"""
        result = {'success': False, 'message': ''}
        
        try:
            from models.ingredient import Ingredient
            
            ingredient = self.db.query(Ingredient).filter(Ingredient.ingredient_id == ingredient_id).first()
            if not ingredient:
                result['message'] = 'Ingredient not found'
                return result
            
            if not ingredient.is_deleted:
                result['message'] = 'Ingredient is not deleted'
                return result
            
            ingredient.restore()
            self.db.commit()
            
            result['success'] = True
            result['message'] = f'Ingredient "{ingredient.name}" restored successfully'
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error restoring ingredient {ingredient_id}: {e}")
            result['message'] = f'Error restoring ingredient: {str(e)}'
        
        return result
    
    def check_user_dependencies(self, user_id: int) -> Dict[str, Any]:
        """Check what depends on a user before deletion"""
        dependencies = {
            'can_delete': True,
            'blocking_records': [],
            'warnings': [],
            'safe_to_delete': []
        }
        
        try:
            # First check if user exists
            user_exists = self.db.execute(text(
                "SELECT COUNT(*) as count FROM users WHERE user_id = :user_id"
            ), {"user_id": user_id}).fetchone()
            
            if not user_exists or user_exists[0] == 0:
                dependencies['can_delete'] = False
                dependencies['error'] = f'User with ID {user_id} does not exist'
                return dependencies
            
            # Check sales as consumer
            consumer_sales = self.db.execute(text(
                "SELECT COUNT(*) as count FROM sales WHERE consumer_id = :user_id"
            ), {"user_id": user_id}).fetchone()
            
            
            if consumer_sales and consumer_sales[0] > 0:
                dependencies['blocking_records'].append({
                    'table': 'sales (as consumer)',
                    'count': consumer_sales[0],
                    'action': 'Cannot delete - would break sales history'
                })
                dependencies['can_delete'] = False
            
            # Check sales as donator
            donator_sales = self.db.execute(text(
                "SELECT COUNT(*) as count FROM sales WHERE donator_id = :user_id"
            ), {"user_id": user_id}).fetchone()
            
            if donator_sales and donator_sales[0] > 0:
                dependencies['warnings'].append({
                    'table': 'sales (as donator)',
                    'count': donator_sales[0],
                    'action': 'Will set donator_id to NULL'
                })
            
            # Check pfand history
            pfand_history = self.db.execute(text(
                "SELECT COUNT(*) as count FROM pfand_history WHERE user_id = :user_id"
            ), {"user_id": user_id}).fetchone()
            
            if pfand_history and pfand_history[0] > 0:
                dependencies['blocking_records'].append({
                    'table': 'pfand_history',
                    'count': pfand_history[0],
                    'action': 'Cannot delete - would break pfand tracking'
                })
                dependencies['can_delete'] = False
            
            # Check transactions
            transactions = self.db.execute(text(
                "SELECT COUNT(*) as count FROM transactions WHERE user_id = :user_id"
            ), {"user_id": user_id}).fetchone()
            
            if transactions and transactions[0] > 0:
                dependencies['blocking_records'].append({
                    'table': 'transactions',
                    'count': transactions[0],
                    'action': 'Cannot delete - would break financial history'
                })
                dependencies['can_delete'] = False
            
        except Exception as e:
            logger.error(f"Error checking user dependencies: {e}")
            dependencies['can_delete'] = False
            dependencies['error'] = str(e)
        
        return dependencies
    
    def check_product_dependencies(self, product_id: int) -> Dict[str, Any]:
        """Check what depends on a product before deletion"""
        dependencies = {
            'can_delete': True,
            'blocking_records': [],
            'warnings': [],
            'safe_to_delete': []
        }
        
        try:
            # First check if product exists
            product_exists = self.db.execute(text(
                "SELECT COUNT(*) as count FROM products WHERE product_id = :product_id"
            ), {"product_id": product_id}).fetchone()
            
            if not product_exists or product_exists[0] == 0:
                dependencies['can_delete'] = False
                dependencies['error'] = f'Product with ID {product_id} does not exist'
                return dependencies
            
            # Check sales
            sales = self.db.execute(text(
                "SELECT COUNT(*) as count FROM sales WHERE product_id = :product_id"
            ), {"product_id": product_id}).fetchone()
            
            if sales and sales[0] > 0:
                dependencies['blocking_records'].append({
                    'table': 'sales',
                    'count': sales[0],
                    'action': 'Cannot delete - would break sales history'
                })
                dependencies['can_delete'] = False
            
            # Check pfand history
            pfand_history = self.db.execute(text(
                "SELECT COUNT(*) as count FROM pfand_history WHERE product_id = :product_id"
            ), {"product_id": product_id}).fetchone()
            
            if pfand_history and pfand_history[0] > 0:
                dependencies['blocking_records'].append({
                    'table': 'pfand_history', 
                    'count': pfand_history[0],
                    'action': 'Cannot delete - would break pfand tracking'
                })
                dependencies['can_delete'] = False
            
            # Check product ingredients (these can be safely deleted)
            ingredients = self.db.execute(text(
                "SELECT COUNT(*) as count FROM product_ingredient WHERE product_id = :product_id"
            ), {"product_id": product_id}).fetchone()
            
            if ingredients and ingredients[0] > 0:
                dependencies['safe_to_delete'].append({
                    'table': 'product_ingredient',
                    'count': ingredients[0],
                    'action': 'Will be automatically deleted (CASCADE)'
                })
            
            # Check toast rounds
            toast_rounds = self.db.execute(text(
                "SELECT COUNT(*) as count FROM product_toastround WHERE product_id = :product_id"
            ), {"product_id": product_id}).fetchone()
            
            if toast_rounds and toast_rounds[0] > 0:
                dependencies['safe_to_delete'].append({
                    'table': 'product_toastround',
                    'count': toast_rounds[0],
                    'action': 'Will be automatically deleted (CASCADE)'
                })
            
        except Exception as e:
            logger.error(f"Error checking product dependencies: {e}")
            dependencies['can_delete'] = False
            dependencies['error'] = str(e)
        
        return dependencies
    
    def check_ingredient_dependencies(self, ingredient_id: int) -> Dict[str, Any]:
        """Check what depends on an ingredient before deletion"""
        dependencies = {
            'can_delete': True,
            'blocking_records': [],
            'warnings': [],
            'safe_to_delete': []
        }
        
        try:
            # First check if ingredient exists
            ingredient_exists = self.db.execute(text(
                "SELECT COUNT(*) as count FROM ingredients WHERE ingredient_id = :ingredient_id"
            ), {"ingredient_id": ingredient_id}).fetchone()
            
            if not ingredient_exists or ingredient_exists[0] == 0:
                dependencies['can_delete'] = False
                dependencies['error'] = f'Ingredient with ID {ingredient_id} does not exist'
                return dependencies
            
            # Check product ingredients
            product_ingredients = self.db.execute(text(
                "SELECT COUNT(*) as count FROM product_ingredient WHERE ingredient_id = :ingredient_id"
            ), {"ingredient_id": ingredient_id}).fetchone()
            
            if product_ingredients and product_ingredients[0] > 0:
                dependencies['blocking_records'].append({
                    'table': 'product_ingredient',
                    'count': product_ingredients[0],
                    'action': 'Cannot delete - products depend on this ingredient'
                })
                dependencies['can_delete'] = False
            
        except Exception as e:
            logger.error(f"Error checking ingredient dependencies: {e}")
            dependencies['can_delete'] = False
            dependencies['error'] = str(e)
        
        return dependencies
    
    def safe_delete_user(self, user_id: int, force: bool = False) -> Dict[str, Any]:
        """Safely delete a user with dependency checks"""
        result = {'success': False, 'message': '', 'details': {}}
        
        try:
            # Check dependencies first
            deps = self.check_user_dependencies(user_id)
            result['details'] = deps
            
            if not deps['can_delete'] and not force:
                result['message'] = 'Cannot delete user - has dependent records'
                return result
            
            if force:
                # Handle nullable foreign keys (set to NULL)
                self.db.execute(text(
                    "UPDATE sales SET donator_id = NULL WHERE donator_id = :user_id"
                ), {"user_id": user_id})
                # Shouldnt we also remove consumer_id?
                # And toust rounds?
                
                result['message'] = 'User deleted with force - some references nullified'
            
            # Delete the user
            deleted_count = self.db.execute(text(
                "DELETE FROM users WHERE user_id = :user_id"
            ), {"user_id": user_id}).rowcount
            
            if deleted_count > 0:
                self.db.commit()
                result['success'] = True
                result['message'] = result.get('message', 'User deleted successfully')
            else:
                result['message'] = 'User not found'
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            result['message'] = f'Error deleting user: {str(e)}'
        
        return result
    
    def safe_delete_product(self, product_id: int, force: bool = False) -> Dict[str, Any]:
        """Safely delete a product with dependency checks"""
        result = {'success': False, 'message': '', 'details': {}}
        
        try:
            # Check dependencies first
            deps = self.check_product_dependencies(product_id)
            result['details'] = deps
            
            if not deps['can_delete'] and not force:
                result['message'] = 'Cannot delete product - has dependent records'
                return result
            
            # Delete related records that can be safely deleted (CASCADE will handle these)
            # The product_ingredient and product_toastround will be deleted automatically
            
            # Delete the product
            deleted_count = self.db.execute(text(
                "DELETE FROM products WHERE product_id = :product_id"
            ), {"product_id": product_id}).rowcount
            
            if deleted_count > 0:
                self.db.commit()
                result['success'] = True
                result['message'] = 'Product deleted successfully'
            else:
                result['message'] = 'Product not found'
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting product {product_id}: {e}")
            result['message'] = f'Error deleting product: {str(e)}'
        
        return result
    
    def safe_delete_ingredient(self, ingredient_id: int, force: bool = False) -> Dict[str, Any]:
        """Safely delete an ingredient with dependency checks"""
        result = {'success': False, 'message': '', 'details': {}}
        
        try:
            # Check dependencies first
            deps = self.check_ingredient_dependencies(ingredient_id)
            result['details'] = deps
            
            if not deps['can_delete'] and not force:
                result['message'] = 'Cannot delete ingredient - products depend on it'
                return result
            
            # Delete the ingredient
            deleted_count = self.db.execute(text(
                "DELETE FROM ingredients WHERE ingredient_id = :ingredient_id"
            ), {"ingredient_id": ingredient_id}).rowcount
            
            if deleted_count > 0:
                self.db.commit()
                result['success'] = True
                result['message'] = 'Ingredient deleted successfully'
            else:
                result['message'] = 'Ingredient not found'
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting ingredient {ingredient_id}: {e}")
            result['message'] = f'Error deleting ingredient: {str(e)}'
        
        return result
