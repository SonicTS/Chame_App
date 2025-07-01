# flexible_deletion_service.py
# Simple deletion service: hard delete only if no dependencies, otherwise soft delete

from sqlalchemy.orm import Session
from typing import Dict, Any, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class CascadeAction(Enum):
    """Available cascade actions for dependencies"""
    # Soft Delete Actions
    CASCADE_SOFT_DELETE = "cascade_soft_delete"  # Also soft delete dependent records
    CASCADE_DISABLE = "cascade_disable"          # Mark dependent records as disabled/broken
    CASCADE_NULLIFY = "cascade_nullify"          # Set foreign key to null (keep record but break link)
    CASCADE_IGNORE = "cascade_ignore"            # Do nothing (preserve historical records)
    CASCADE_RESTRICT = "cascade_restrict"        # Prevent deletion if dependencies exist
    
    # Hard Delete Actions  
    CASCADE_HARD_DELETE = "cascade_hard_delete"  # Also permanently delete dependent records
    CASCADE_SOFT_DELETE_DEPS = "cascade_soft_delete_deps"  # Soft delete deps but hard delete main
    CASCADE_NULLIFY_HARD = "cascade_nullify_hard"  # Set FK to null, keep dependent records


@dataclass
class DependencyInfo:
    """Information about a dependency relationship"""
    table_name: str
    relationship_name: str
    count: int
    sample_records: List[Dict[str, Any]]
    is_critical: bool  # Whether this dependency prevents deletion
    default_action: CascadeAction
    available_actions: List[CascadeAction]
    description: str


@dataclass
class DeletionPlan:
    """Plan for deletion with user-chosen cascade actions"""
    entity_type: str
    entity_id: int
    entity_name: str
    deletion_type: str  # 'soft' or 'hard'
    dependencies: List[DependencyInfo]
    user_choices: Dict[str, CascadeAction]  # relationship_name -> chosen action
    can_proceed: bool
    warnings: List[str]
    errors: List[str]


class FlexibleDeletionService:
    """Service for handling simple deletion logic: hard delete only if no dependencies, otherwise soft delete"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def analyze_deletion_impact(self, entity_type: str, entity_id: int) -> DeletionPlan:
        """
        Analyze what would be impacted by deleting an entity
        Simplified logic:
        - Hard deletion only if NO dependencies exist
        - If dependencies exist, MUST use soft deletion
        - For ingredients: soft deletion always cascades to all products using it
        """
        if entity_type == 'ingredient':
            return self._analyze_ingredient_deletion(entity_id)
        elif entity_type == 'product':
            return self._analyze_product_deletion(entity_id)
        elif entity_type == 'user':
            return self._analyze_user_deletion(entity_id)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
    
    def _analyze_ingredient_deletion(self, ingredient_id: int) -> DeletionPlan:
        """
        Analyze impact of deleting an ingredient
        Simplified logic: If ingredient is used in products, MUST soft delete and cascade to products
        If no products use it, can hard delete
        """
        from models.ingredient import Ingredient
        from models.product_ingredient_table import ProductIngredient
        
        print(f"DEBUG: Analyzing deletion impact for ingredient {ingredient_id}")
        
        ingredient = self.session.query(Ingredient).filter(
            Ingredient.ingredient_id == ingredient_id
        ).first()
        
        if not ingredient:
            print(f"DEBUG: Ingredient {ingredient_id} not found")
            return DeletionPlan(
                entity_type='ingredient',
                entity_id=ingredient_id,
                entity_name='Unknown',
                deletion_type='soft',
                dependencies=[],
                user_choices={},
                can_proceed=False,
                warnings=[],
                errors=[f'Ingredient with ID {ingredient_id} not found']
            )
        
        print(f"DEBUG: Found ingredient: {ingredient.name}")
        dependencies = []
        deletion_type = 'hard'  # Default to hard deletion
        warnings = []
        
        # Check if ingredient is used in any products
        product_ingredients = self.session.query(ProductIngredient).filter(
            ProductIngredient.ingredient_id == ingredient_id
        ).all()
        
        print(f"DEBUG: Found {len(product_ingredients)} product-ingredient relationships")
        
        if product_ingredients:
            # Has dependencies - must use soft deletion
            deletion_type = 'soft'
            
            # Get unique products affected
            affected_products = []
            product_ids_seen = set()
            
            for pi in product_ingredients:
                if pi.product and pi.product.product_id not in product_ids_seen:
                    affected_products.append(pi.product)
                    product_ids_seen.add(pi.product.product_id)
            
            print(f"DEBUG: Found {len(affected_products)} unique affected products")
            
            # For simplicity: when ingredient is soft deleted, all products using it must also be soft deleted
            product_samples = []
            for product in affected_products[:5]:  # Show first 5 as samples
                product_samples.append({
                    'product_name': product.name,
                    'product_id': product.product_id,
                    'category': product.category,
                    'current_stock': product.stock_quantity
                })
                print(f"DEBUG: Added product sample: {product.name}")
            
            dependencies.append(DependencyInfo(
                table_name='products',
                relationship_name='affected_products',
                count=len(affected_products),
                sample_records=product_samples,
                is_critical=True,
                default_action=CascadeAction.CASCADE_SOFT_DELETE,  # Always cascade soft delete
                available_actions=[CascadeAction.CASCADE_SOFT_DELETE],  # Only one option
                description=f"Products that use this ingredient will also be soft deleted ({len(affected_products)} products)"
            ))
            
            warnings.append(f"This ingredient is used in {len(affected_products)} products. All affected products will also be soft deleted.")
        else:
            print("DEBUG: No product-ingredient relationships found - can hard delete")
            warnings.append("No products use this ingredient. It can be permanently deleted.")
        
        plan = DeletionPlan(
            entity_type='ingredient',
            entity_id=ingredient_id,
            entity_name=ingredient.name,
            deletion_type=deletion_type,
            dependencies=dependencies,
            user_choices={},
            can_proceed=True,
            warnings=warnings,
            errors=[]
        )
        
        print(f"DEBUG: Created deletion plan with {len(dependencies)} dependencies, deletion_type={deletion_type}")
        return plan
    
    def _analyze_product_deletion(self, product_id: int) -> DeletionPlan:
        """
        Analyze impact of deleting a product
        Simplified logic: If product has sales history, MUST soft delete. If no history, can hard delete.
        """
        from models.product_table import Product
        from models.sales_table import Sale
        
        product = self.session.query(Product).filter(
            Product.product_id == product_id
        ).first()
        
        if not product:
            return DeletionPlan(
                entity_type='product',
                entity_id=product_id,
                entity_name='Unknown',
                deletion_type='soft',
                dependencies=[],
                user_choices={},
                can_proceed=False,
                warnings=[],
                errors=[f'Product with ID {product_id} not found']
            )
        
        dependencies = []
        deletion_type = 'hard'  # Default to hard deletion
        warnings = []
        
        # Check if product has sales history - simplified logic
        sales = self.session.query(Sale).filter(Sale.product_id == product_id).all()
        
        if sales:
            # Has sales history - must use soft deletion
            deletion_type = 'soft'
            
            sample_records = []
            for sale in sales[:5]:  # Show first 5 as samples
                sample_records.append({
                    'sale_id': sale.sale_id,
                    'consumer_name': sale.consumer.name if sale.consumer else 'Unknown',
                    'quantity': sale.quantity,
                    'timestamp': str(sale.timestamp)
                })
            
            dependencies.append(DependencyInfo(
                table_name='sales',
                relationship_name='sales',
                count=len(sales),
                sample_records=sample_records,
                is_critical=True,
                default_action=CascadeAction.CASCADE_IGNORE,  # Keep sales history
                available_actions=[CascadeAction.CASCADE_IGNORE],  # Only one option
                description=f"Product has sales history and can only be soft deleted ({len(sales)} sales)"
            ))
            
            warnings.append(f"This product has {len(sales)} sales records. It can only be soft deleted to preserve sales history.")
        else:
            warnings.append("No sales history found. Product can be permanently deleted.")
        
        return DeletionPlan(
            entity_type='product',
            entity_id=product_id,
            entity_name=product.name,
            deletion_type=deletion_type,
            dependencies=dependencies,
            user_choices={},
            can_proceed=True,
            warnings=warnings,
            errors=[]
        )
    
    def _analyze_user_deletion(self, user_id: int) -> DeletionPlan:
        """
        Analyze impact of deleting a user
        Simplified logic: If user has sales/transaction history, MUST soft delete. If no history, can hard delete.
        """
        from models.user_table import User
        from models.sales_table import Sale
        from models.transaction_table import Transaction
        
        user = self.session.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return DeletionPlan(
                entity_type='user',
                entity_id=user_id,
                entity_name='Unknown',
                deletion_type='soft',
                dependencies=[],
                user_choices={},
                can_proceed=False,
                warnings=[],
                errors=[f'User with ID {user_id} not found']
            )
        
        dependencies = []
        deletion_type = 'hard'  # Default to hard deletion
        warnings = []
        
        # Check sales history
        sales = self.session.query(Sale).filter(Sale.consumer_id == user_id).all()
        
        # Check transaction history
        transactions = self.session.query(Transaction).filter(Transaction.user_id == user_id).all()
        
        total_history_count = len(sales) + len(transactions)
        
        if total_history_count > 0:
            # Has history - must use soft deletion
            deletion_type = 'soft'
            
            if sales:
                sample_sales = []
                for sale in sales[:3]:
                    sample_sales.append({
                        'sale_id': sale.sale_id,
                        'product_name': sale.product.name if sale.product else 'Unknown',
                        'quantity': sale.quantity,
                        'timestamp': str(sale.timestamp)
                    })
                
                dependencies.append(DependencyInfo(
                    table_name='sales',
                    relationship_name='sales',
                    count=len(sales),
                    sample_records=sample_sales,
                    is_critical=True,
                    default_action=CascadeAction.CASCADE_IGNORE,
                    available_actions=[CascadeAction.CASCADE_IGNORE],
                    description=f"User has sales history ({len(sales)} sales)"
                ))
            
            if transactions:
                sample_transactions = []
                for trans in transactions[:3]:
                    sample_transactions.append({
                        'transaction_id': trans.transaction_id,
                        'amount': trans.amount,
                        'transaction_type': trans.type,
                        'timestamp': str(trans.timestamp)
                    })
                
                dependencies.append(DependencyInfo(
                    table_name='transactions',
                    relationship_name='transactions',
                    count=len(transactions),
                    sample_records=sample_transactions,
                    is_critical=True,
                    default_action=CascadeAction.CASCADE_IGNORE,
                    available_actions=[CascadeAction.CASCADE_IGNORE],
                    description=f"User has transaction history ({len(transactions)} transactions)"
                ))
            
            warnings.append(f"This user has {total_history_count} records (sales/transactions). It can only be soft deleted to preserve history.")
        else:
            warnings.append("No sales or transaction history found. User can be permanently deleted.")
        
        return DeletionPlan(
            entity_type='user',
            entity_id=user_id,
            entity_name=user.name,
            deletion_type=deletion_type,
            dependencies=dependencies,
            user_choices={},
            can_proceed=True,
            warnings=warnings,
            errors=[]
        )
    
    def execute_deletion_plan(self, plan: DeletionPlan, deleted_by_user: str = "system") -> Dict[str, Any]:
        """
        Execute a deletion plan with simplified logic
        """
        result = {'success': False, 'message': '', 'details': {}, 'affected_records': {}}
        
        if not plan.can_proceed:
            result['message'] = f"Cannot proceed with deletion: {'; '.join(plan.errors)}"
            return result
        
        try:
            if plan.deletion_type == 'soft':
                return self._execute_soft_deletion_simple(plan, deleted_by_user)
            else:
                return self._execute_hard_deletion_simple(plan)
                
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error executing deletion plan: {e}")
            result['message'] = f'Error executing deletion: {str(e)}'
            return result
        
    def _execute_soft_deletion_simple(self, plan: DeletionPlan, deleted_by_user: str) -> Dict[str, Any]:
        """
        Execute soft deletion with simplified logic
        For ingredients: soft delete ingredient and cascade to all products using it
        For products/users: only soft delete the entity (dependencies are preserved)
        """
        result = {'success': False, 'message': '', 'details': {}, 'affected_records': {}}
        affected_records = {}
        
        try:
            # Get the main entity
            entity = self._get_entity(plan.entity_type, plan.entity_id)
            if not entity:
                result['message'] = f'{plan.entity_type.title()} not found'
                return result
            
            # Special case for ingredients: cascade to products
            if plan.entity_type == 'ingredient':
                # Find and soft delete all products using this ingredient
                from models.product_ingredient_table import ProductIngredient
                from models.product_table import Product
                
                product_ingredient_records = self.session.query(ProductIngredient).filter(
                    ProductIngredient.ingredient_id == entity.ingredient_id
                ).all()
                
                product_ids = [pi.product_id for pi in product_ingredient_records if pi.product_id]
                products = self.session.query(Product).filter(Product.product_id.in_(product_ids)).all()
                
                # Soft delete all affected products first
                products_deleted = 0
                for product in products:
                    if hasattr(product, 'soft_delete') and not getattr(product, 'is_deleted', False):
                        product.soft_delete(deleted_by_user, session=self.session, cascade=False)
                        products_deleted += 1
                
                affected_records['affected_products'] = {
                    'action': 'cascade_soft_delete',
                    'count': products_deleted
                }
            
            # Soft delete the main entity
            if hasattr(entity, 'soft_delete'):
                entity.soft_delete(deleted_by_user, session=self.session, cascade=False)
            else:
                # Fallback for entities without soft delete mixin
                entity.is_deleted = True
                entity.deleted_at = datetime.now(timezone.utc)
                entity.deleted_by = deleted_by_user
            
            affected_records['main_entity'] = {
                'action': 'soft_delete',
                'count': 1
            }
            
            self.session.commit()
            
            result['success'] = True
            result['message'] = f'{plan.entity_type.title()} "{plan.entity_name}" soft deleted successfully'
            result['affected_records'] = affected_records
            
        except Exception as e:
            self.session.rollback()
            raise e
        
        return result
    
    def _execute_hard_deletion_simple(self, plan: DeletionPlan) -> Dict[str, Any]:
        """
        Execute hard deletion - only used when no dependencies exist
        """
        result = {'success': False, 'message': '', 'details': {}, 'affected_records': {}}
        
        try:
            # Get the main entity
            entity = self._get_entity(plan.entity_type, plan.entity_id)
            if not entity:
                result['message'] = f'{plan.entity_type.title()} not found'
                return result
            
            # Hard delete the entity (for hard deletion, we don't track who deleted it)
            self.session.delete(entity)
            self.session.commit()
            
            result['success'] = True
            result['message'] = f'{plan.entity_type.title()} "{plan.entity_name}" permanently deleted'
            result['affected_records'] = {'main_entity': {'action': 'hard_delete', 'count': 1}}
            
        except Exception as e:
            self.session.rollback()
            raise e
        
        return result

    def _execute_soft_deletion(self, plan: DeletionPlan, deleted_by_user: str) -> Dict[str, Any]:
        """Execute soft deletion with user-chosen cascade actions"""
        result = {'success': False, 'message': '', 'details': {}, 'affected_records': {}}
        affected_records = {}
        
        try:
            # Get the main entity
            entity = self._get_entity(plan.entity_type, plan.entity_id)
            if not entity:
                result['message'] = f'{plan.entity_type.title()} not found'
                return result
            
            # Process each dependency according to user choice
            main_entity_action = CascadeAction.CASCADE_SOFT_DELETE  # Default action
            for dep in plan.dependencies:
                action = plan.user_choices.get(dep.relationship_name, dep.default_action)
                
                # Handle special case for self-reference (main entity action)
                if dep.relationship_name == 'self':
                    main_entity_action = action
                    continue
                
                # For product sales dependency, the action also determines what happens to the product
                if plan.entity_type == 'product' and dep.relationship_name == 'sales':
                    main_entity_action = action
                    # Don't actually modify sales records, just use the action for the product
                    affected_records[dep.relationship_name] = {
                        'action': action.value,
                        'count': 0  # No sales records are modified
                    }
                    continue
                    
                affected_count = self._apply_cascade_action(entity, dep, action, deleted_by_user, 'soft')
                affected_records[dep.relationship_name] = {
                    'action': action.value,
                    'count': affected_count
                }
            
            # Apply action to the main entity based on user choice
            if main_entity_action == CascadeAction.CASCADE_DISABLE:
                # Mark as disabled/broken instead of deleted
                if hasattr(entity, 'disable'):
                    entity.disable("Marked as broken/out of stock")
                    affected_records['main_entity'] = {
                        'action': main_entity_action.value,
                        'count': 1
                    }
                else:
                    # Fallback to soft delete if disable not supported
                    main_entity_action = CascadeAction.CASCADE_SOFT_DELETE
            
            elif main_entity_action == CascadeAction.CASCADE_IGNORE:
                # Do nothing to the main entity - leave it as is
                affected_records['main_entity'] = {
                    'action': main_entity_action.value,
                    'count': 0
                }
            
            elif main_entity_action == CascadeAction.CASCADE_RESTRICT:
                # This should have been caught earlier, but just in case
                result['message'] = f'Cannot delete {plan.entity_type} - deletion was restricted'
                return result
            
            if main_entity_action not in [CascadeAction.CASCADE_DISABLE, CascadeAction.CASCADE_IGNORE, CascadeAction.CASCADE_RESTRICT]:
                # Standard soft delete the main entity
                if hasattr(entity, 'soft_delete'):
                    entity.soft_delete(deleted_by_user, session=self.session, cascade=False)
                else:
                    # Fallback for entities without soft delete mixin
                    entity.is_deleted = True
                    entity.deleted_at = datetime.now(timezone.utc)
                    entity.deleted_by = deleted_by_user
                
                affected_records['main_entity'] = {
                    'action': 'cascade_soft_delete',
                    'count': 1
                }
            
            self.session.commit()
            
            result['success'] = True
            result['message'] = f'{plan.entity_type.title()} "{plan.entity_name}" soft deleted successfully'
            result['affected_records'] = affected_records
            
        except Exception as e:
            self.session.rollback()
            raise e
        
        return result
    
    def _execute_hard_deletion(self, plan: DeletionPlan, deleted_by_user: str) -> Dict[str, Any]:
        """Execute hard deletion with user-chosen cascade actions"""
        result = {'success': False, 'message': '', 'details': {}, 'affected_records': {}}
        affected_records = {}
        
        try:
            # Get the main entity
            entity = self._get_entity(plan.entity_type, plan.entity_id)
            if not entity:
                result['message'] = f'{plan.entity_type.title()} not found'
                return result
            
            # Process dependencies in reverse order for hard deletion
            for dep in reversed(plan.dependencies):
                action = plan.user_choices.get(dep.relationship_name, dep.default_action)
                affected_count = self._apply_cascade_action(entity, dep, action, deleted_by_user, 'hard')
                affected_records[dep.relationship_name] = {
                    'action': action.value,
                    'count': affected_count
                }
            
            # Finally, hard delete the main entity
            self.session.delete(entity)
            self.session.commit()
            
            result['success'] = True
            result['message'] = f'{plan.entity_type.title()} "{plan.entity_name}" permanently deleted'
            result['affected_records'] = affected_records
            
        except Exception as e:
            self.session.rollback()
            raise e
        
        return result
    
    def _apply_cascade_action(self, entity, dependency: DependencyInfo, 
                            action: CascadeAction, deleted_by_user: str, deletion_type: str) -> int:
        """Apply a specific cascade action to dependent records"""
        affected_count = 0
        
        print(f"DEBUG: Applying cascade action {action.value} to {dependency.relationship_name}")
        
        # Handle different dependency types
        if dependency.relationship_name == 'ingredient_products':
            # Handle product-ingredient relationships
            try:
                from models.product_ingredient_table import ProductIngredient
                related_records = self.session.query(ProductIngredient).filter(
                    ProductIngredient.ingredient_id == entity.ingredient_id
                ).all()
                print(f"DEBUG: Got {len(related_records)} product-ingredient records")
            except Exception as e:
                print(f"DEBUG: Failed to get product-ingredient records: {e}")
                return 0
                
            for record in related_records:
                if not record:
                    continue
                    
                if action == CascadeAction.CASCADE_NULLIFY:
                    # Remove the product-ingredient relationship
                    self.session.delete(record)
                    affected_count += 1
                    print(f"DEBUG: Deleted product-ingredient relationship for product {record.product_id}")
                    
                # CASCADE_RESTRICT doesn't modify records
                    
        elif dependency.relationship_name == 'affected_products':
            # Handle the affected products themselves
            try:
                from models.product_ingredient_table import ProductIngredient
                from models.product_table import Product
                
                # Get products that use this ingredient
                product_ingredient_records = self.session.query(ProductIngredient).filter(
                    ProductIngredient.ingredient_id == entity.ingredient_id
                ).all()
                
                product_ids = [pi.product_id for pi in product_ingredient_records if pi.product_id]
                products = self.session.query(Product).filter(Product.product_id.in_(product_ids)).all()
                print(f"DEBUG: Got {len(products)} affected products")
                
            except Exception as e:
                print(f"DEBUG: Failed to get affected products: {e}")
                return 0
                
            for product in products:
                if not product:
                    continue
                    
                print(f"DEBUG: Processing product {product.name} for action {action.value}")
                    
                if action == CascadeAction.CASCADE_SOFT_DELETE:
                    if hasattr(product, 'soft_delete'):
                        product.soft_delete(deleted_by_user, session=self.session, cascade=False)
                        affected_count += 1
                        print(f"DEBUG: Soft deleted product {product.name}")
                        
                elif action == CascadeAction.CASCADE_DISABLE:
                    if hasattr(product, 'disable'):
                        product.disable(f"Required ingredient {entity.name} was deleted")
                        affected_count += 1
                        print(f"DEBUG: Disabled product {product.name}")
                        
                elif action == CascadeAction.CASCADE_HARD_DELETE:
                    if deletion_type == 'hard':
                        self.session.delete(product)
                        affected_count += 1
                        print(f"DEBUG: Hard deleted product {product.name}")
                        
                # CASCADE_RESTRICT doesn't modify records
                
        else:
            # Handle other relationships (original logic)
            try:
                related_records = getattr(entity, dependency.relationship_name, None)
                print(f"DEBUG: Got {len(related_records) if related_records else 0} related records via getattr")
            except Exception as e:
                print(f"DEBUG: Failed to get relationship via getattr: {e}")
                related_records = []
            
            if not related_records:
                print(f"DEBUG: No related records found for {dependency.relationship_name}")
                return 0
                
            if not isinstance(related_records, list):
                related_records = [related_records] if related_records else []
            
            for record in related_records:
                if not record:
                    continue
                    
                print(f"DEBUG: Processing record of type {type(record).__name__}")
                    
                if action == CascadeAction.CASCADE_SOFT_DELETE:
                    if hasattr(record, 'soft_delete'):
                        record.soft_delete(deleted_by_user, session=self.session, cascade=False)
                        affected_count += 1
                        
                elif action == CascadeAction.CASCADE_DISABLE:
                    if hasattr(record, 'disable'):
                        record.disable(f"Related {entity.__class__.__name__} was deleted")
                        affected_count += 1
                        
                elif action == CascadeAction.CASCADE_NULLIFY:
                    # Set foreign key to null for other relationships
                    # This would need to be customized based on the specific relationship
                    pass
                    
                elif action == CascadeAction.CASCADE_HARD_DELETE:
                    if deletion_type == 'hard':
                        self.session.delete(record)
                        affected_count += 1
        
        print(f"DEBUG: Affected {affected_count} records")
        return affected_count
    
    def _get_entity(self, entity_type: str, entity_id: int):
        """Get entity by type and ID"""
        if entity_type == 'ingredient':
            from models.ingredient import Ingredient
            return self.session.query(Ingredient).filter(
                Ingredient.ingredient_id == entity_id
            ).first()
        elif entity_type == 'product':
            from models.product_table import Product
            return self.session.query(Product).filter(
                Product.product_id == entity_id
            ).first()
        elif entity_type == 'user':
            from models.user_table import User
            return self.session.query(User).filter(
                User.user_id == entity_id
            ).first()
        else:
            return None
    
    def get_cascade_action_description(self, action: CascadeAction, entity_type: str, dependency_name: str) -> str:
        """Get human-readable description of what a cascade action will do"""
        descriptions = {
            CascadeAction.CASCADE_SOFT_DELETE: f"Also mark related {dependency_name} as deleted (can be restored later)",
            CascadeAction.CASCADE_DISABLE: f"Mark related {dependency_name} as disabled/broken (keeps records but makes them unavailable)",
            CascadeAction.CASCADE_NULLIFY: f"Remove the connection to this {entity_type} but keep the related {dependency_name}",
            CascadeAction.CASCADE_IGNORE: f"Keep related {dependency_name} exactly as they are (recommended for historical data)",
            CascadeAction.CASCADE_RESTRICT: f"Prevent deletion because related {dependency_name} exist",
            CascadeAction.CASCADE_HARD_DELETE: f"Permanently delete related {dependency_name} (cannot be undone)",
            CascadeAction.CASCADE_SOFT_DELETE_DEPS: f"Mark related {dependency_name} as deleted but permanently delete the {entity_type}",
            CascadeAction.CASCADE_NULLIFY_HARD: f"Remove connections but keep related {dependency_name}, permanently delete the {entity_type}"
        }
        return descriptions.get(action, "Unknown action")
