# enhanced_deletion_service.py
# Service for handling enhanced soft deletion operations

from sqlalchemy.orm import Session
from typing import List, Optional
from models.enhanced_soft_delete_mixin import EnhancedSoftDeleteMixin
from models.ingredient import Ingredient
from models.product_table import Product
from models.user_table import User
from utils.firebase_logger import log_info, log_error, log_debug


class EnhancedDeletionService:
    """Service for handling enhanced soft deletion with cascading"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def soft_delete_ingredient(self, ingredient_id: int, deleted_by_user: str = "system") -> bool:
        """
        Soft delete an ingredient and handle cascading to products
        
        When an ingredient is deleted:
        - The ingredient is marked as deleted
        - All products using this ingredient are disabled (marked unavailable)
        - This prevents the products from being sold but preserves historical data
        """
        try:
            ingredient = self.session.query(Ingredient).filter(
                Ingredient.ingredient_id == ingredient_id,
                ~Ingredient.is_deleted
            ).first()
            
            if not ingredient:
                log_error(f"Ingredient {ingredient_id} not found or already deleted")
                return False
            
            log_info(f"Soft deleting ingredient: {ingredient.name} (ID: {ingredient_id})")
            
            # Perform soft delete with cascading
            ingredient.soft_delete(deleted_by_user, self.session, cascade=True)
            
            # Commit the changes
            self.session.commit()
            log_info(f"Successfully soft deleted ingredient {ingredient_id} and cascaded to dependent products")
            return True
            
        except Exception as e:
            self.session.rollback()
            log_error(f"Failed to soft delete ingredient {ingredient_id}", exception=e)
            return False
    
    def soft_delete_product(self, product_id: int, deleted_by_user: str = "system") -> bool:
        """
        Soft delete a product
        
        When a product is deleted:
        - The product is marked as deleted
        - Sales history is preserved (CASCADE_IGNORE)
        - Pfand history is preserved (CASCADE_IGNORE)
        """
        try:
            product = self.session.query(Product).filter(
                Product.product_id == product_id,
                ~Product.is_deleted
            ).first()
            
            if not product:
                log_error(f"Product {product_id} not found or already deleted")
                return False
            
            log_info(f"Soft deleting product: {product.name} (ID: {product_id})")
            
            # Perform soft delete with cascading
            product.soft_delete(deleted_by_user, self.session, cascade=True)
            
            # Commit the changes
            self.session.commit()
            log_info(f"Successfully soft deleted product {product_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            log_error(f"Failed to soft delete product {product_id}", exception=e)
            return False
    
    def soft_delete_user(self, user_id: int, deleted_by_user: str = "system") -> bool:
        """
        Soft delete a user
        
        When a user is deleted:
        - The user is marked as deleted
        - All historical data (sales, donations, pfand history) is preserved
        """
        try:
            user = self.session.query(User).filter(
                User.user_id == user_id,
                ~User.is_deleted
            ).first()
            
            if not user:
                log_error(f"User {user_id} not found or already deleted")
                return False
            
            log_info(f"Soft deleting user: {user.name} (ID: {user_id})")
            
            # Perform soft delete with cascading
            user.soft_delete(deleted_by_user, self.session, cascade=True)
            
            # Commit the changes
            self.session.commit()
            log_info(f"Successfully soft deleted user {user_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            log_error(f"Failed to soft delete user {user_id}", exception=e)
            return False
    
    def restore_item(self, model_class, item_id: int) -> bool:
        """
        Restore a soft-deleted item
        """
        try:
            # Get the primary key column name
            pk_column = model_class.__table__.primary_key.columns.values()[0]
            
            item = self.session.query(model_class).filter(
                pk_column == item_id,
                model_class.is_deleted == True
            ).first()
            
            if not item:
                log_error(f"{model_class.__name__} {item_id} not found or not deleted")
                return False
            
            log_info(f"Restoring {model_class.__name__}: {getattr(item, 'name', item_id)} (ID: {item_id})")
            
            # Restore the item
            item.restore()
            
            # Commit the changes
            self.session.commit()
            log_info(f"Successfully restored {model_class.__name__} {item_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            log_error(f"Failed to restore {model_class.__name__} {item_id}", exception=e)
            return False
    
    def get_available_products(self) -> List[Product]:
        """Get all available products (not deleted and not disabled)"""
        return self.session.query(Product).filter(
            ~Product.is_deleted,
            ~Product.is_disabled
        ).all()
    
    def get_available_ingredients(self) -> List[Ingredient]:
        """Get all available ingredients (not deleted and not disabled)"""
        return self.session.query(Ingredient).filter(
            ~Ingredient.is_deleted,
            ~Ingredient.is_disabled
        ).all()
    
    def get_available_users(self) -> List[User]:
        """Get all available users (not deleted and not disabled)"""
        return self.session.query(User).filter(
            ~User.is_deleted,
            ~User.is_disabled
        ).all()
    
    def get_disabled_products_by_ingredient(self, ingredient_id: int) -> List[Product]:
        """Get products that were disabled due to a specific ingredient being deleted"""
        return self.session.query(Product).filter(
            Product.is_disabled == True,
            Product.disabled_reason.like(f"%{ingredient_id}%")  # This would need refinement
        ).all()
    
    def check_product_availability(self, product_id: int) -> dict:
        """
        Check if a product is available and why it might not be
        
        Returns:
        {
            'available': bool,
            'deleted': bool,
            'disabled': bool,
            'disabled_reason': str,
            'unavailable_ingredients': list
        }
        """
        try:
            product = self.session.query(Product).filter(
                Product.product_id == product_id
            ).first()
            
            if not product:
                return {
                    'available': False,
                    'deleted': False,
                    'disabled': False,
                    'disabled_reason': 'Product not found',
                    'unavailable_ingredients': []
                }
            
            # Check for unavailable ingredients
            unavailable_ingredients = []
            if hasattr(product, 'get_filtered_relationship'):
                product_ingredients = product.get_filtered_relationship('product_ingredients', 
                                                                      include_deleted=True, 
                                                                      include_disabled=True)
                for pi in product_ingredients:
                    if pi.ingredient and not pi.ingredient.is_available:
                        unavailable_ingredients.append({
                            'id': pi.ingredient.ingredient_id,
                            'name': pi.ingredient.name,
                            'deleted': pi.ingredient.is_deleted,
                            'disabled': pi.ingredient.is_disabled
                        })
            
            return {
                'available': product.is_available,
                'deleted': product.is_deleted,
                'disabled': product.is_disabled,
                'disabled_reason': getattr(product, 'disabled_reason', None),
                'unavailable_ingredients': unavailable_ingredients
            }
            
        except Exception as e:
            log_error(f"Failed to check product availability for {product_id}", exception=e)
            return {
                'available': False,
                'deleted': False,
                'disabled': False,
                'disabled_reason': 'Error checking availability',
                'unavailable_ingredients': []
            }
    
    def get_deleted_products(self) -> List[dict]:
        """Get all soft-deleted products"""
        try:
            deleted_products = self.session.query(Product).filter(
                Product.is_deleted
            ).all()
            
            return [product.to_dict() for product in deleted_products]
            
        except Exception as e:
            log_error("Failed to get deleted products", exception=e)
            return []
    
    def get_deleted_ingredients(self) -> List[dict]:
        """Get all soft-deleted ingredients"""
        try:
            deleted_ingredients = self.session.query(Ingredient).filter(
                Ingredient.is_deleted
            ).all()
            
            return [ingredient.to_dict() for ingredient in deleted_ingredients]
            
        except Exception as e:
            log_error("Failed to get deleted ingredients", exception=e)
            return []
    
    def get_deleted_users(self) -> List[dict]:
        """Get all soft-deleted users"""
        try:
            deleted_users = self.session.query(User).filter(
                User.is_deleted
            ).all()
            
            return [user.to_dict() for user in deleted_users]
            
        except Exception as e:
            log_error("Failed to get deleted users", exception=e)
            return []
    
    def restore_product(self, product_id: int) -> bool:
        """Restore a soft-deleted product"""
        return self.restore_item(Product, product_id)
    
    def restore_ingredient(self, ingredient_id: int) -> bool:
        """Restore a soft-deleted ingredient"""
        return self.restore_item(Ingredient, ingredient_id)
    
    def restore_user(self, user_id: int) -> bool:
        """Restore a soft-deleted user"""
        return self.restore_item(User, user_id)

        # ...existing code...
