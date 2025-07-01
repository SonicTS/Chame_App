# enhanced_soft_delete_mixin.py
# Enhanced mixin to add comprehensive soft delete functionality with cascading

from sqlalchemy import Column, Boolean, DateTime, String
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Callable
from utils.firebase_logger import log_debug, log_error, log_info

class SoftDeleteCascadeRule:
    """Defines how soft deletes should cascade to related models"""
    
    CASCADE_SOFT_DELETE = "cascade_soft_delete"  # Also soft delete related records
    CASCADE_DISABLE = "cascade_disable"  # Mark related records as disabled/unavailable
    CASCADE_NULLIFY = "cascade_nullify"  # Set foreign key to null
    CASCADE_RESTRICT = "cascade_restrict"  # Prevent deletion if related records exist
    CASCADE_IGNORE = "cascade_ignore"  # Do nothing (for historical records like sales)
    
    def __init__(self, relationship_name: str, cascade_type: str, 
                 condition_callback: Optional[Callable] = None,
                 custom_handler: Optional[Callable] = None):
        self.relationship_name = relationship_name
        self.cascade_type = cascade_type
        self.condition_callback = condition_callback  # Optional condition to check before cascading
        self.custom_handler = custom_handler  # Custom function to handle the cascade


class HardDeleteCascadeRule:
    """Defines how hard deletes should cascade to related models"""
    
    CASCADE_HARD_DELETE = "cascade_hard_delete"  # Also hard delete related records
    CASCADE_NULLIFY = "cascade_nullify"  # Set foreign key to null (preserve records)
    CASCADE_RESTRICT = "cascade_restrict"  # Prevent deletion if related records exist
    CASCADE_SOFT_DELETE = "cascade_soft_delete"  # Soft delete related records instead
    
    def __init__(self, relationship_name: str, cascade_type: str,
                 condition_callback: Optional[Callable] = None,
                 custom_handler: Optional[Callable] = None,
                 cascade_order: int = 0):  # Order for cascading (lower numbers first)
        self.relationship_name = relationship_name
        self.cascade_type = cascade_type
        self.condition_callback = condition_callback
        self.custom_handler = custom_handler
        self.cascade_order = cascade_order


class EnhancedSoftDeleteMixin:
    """Enhanced mixin to add soft delete functionality with cascading rules"""
    
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String, nullable=True)
    is_disabled = Column(Boolean, default=False, nullable=False)  # For cascade_disable
    disabled_reason = Column(String, nullable=True)  # Why it was disabled
    
    # Class-level cascade rules - to be defined in each model
    _cascade_rules: List[SoftDeleteCascadeRule] = []
    _hard_delete_rules: List[HardDeleteCascadeRule] = []
    
    def soft_delete(self, deleted_by_user=None, session=None, cascade=True):
        """Mark the record as deleted and handle cascading"""
        if self.is_deleted:
            log_debug(f"Record {self.__class__.__name__}:{getattr(self, 'id', 'unknown')} already deleted")
            return
            
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by_user
        
        log_info(f"Soft deleting {self.__class__.__name__}:{getattr(self, 'id', 'unknown')}")
        
        if cascade and session:
            self._handle_cascade_on_delete(session, deleted_by_user)
    
    def restore(self):
        """Restore a soft-deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.is_disabled = False
        self.disabled_reason = None
        
        log_info(f"Restoring {self.__class__.__name__}:{getattr(self, 'id', 'unknown')}")
    
    def disable(self, reason="Related record deleted"):
        """Mark record as disabled (for cascade_disable)"""
        self.is_disabled = True
        self.disabled_reason = reason
        
        log_info(f"Disabling {self.__class__.__name__}:{getattr(self, 'id', 'unknown')} - {reason}")
    
    def enable(self):
        """Re-enable a disabled record"""
        self.is_disabled = False
        self.disabled_reason = None
    
    @property
    def is_available(self):
        """Check if record is available (not deleted and not disabled)"""
        return not self.is_deleted and not self.is_disabled
    
    def hard_delete(self, session: Session, deleted_by_user: str = "system", force: bool = False):
        """
        Permanently delete the record and handle cascading
        
        Args:
            session: Database session
            deleted_by_user: Who initiated the deletion
            force: If True, bypasses restrict rules (dangerous!)
        """
        if not force:
            # Check restrict rules first
            self._check_hard_delete_restrictions(session)
        
        log_info(f"Hard deleting {self.__class__.__name__}:{getattr(self, 'id', 'unknown')}")
        
        # Process cascading rules in order
        self._handle_cascade_on_hard_delete(session, deleted_by_user, force)
        
        # Finally, delete this record
        session.delete(self)
        session.flush()  # Ensure deletion is processed
    
    def _check_hard_delete_restrictions(self, session: Session):
        """Check if hard delete is allowed based on restrict rules"""
        for rule in sorted(self._hard_delete_rules, key=lambda r: r.cascade_order):
            if rule.cascade_type == HardDeleteCascadeRule.CASCADE_RESTRICT:
                related_objects = getattr(self, rule.relationship_name, None)
                if not related_objects:
                    continue
                
                # Handle single object vs collection
                if not isinstance(related_objects, list):
                    related_objects = [related_objects]
                
                active_related = []
                for obj in related_objects:
                    if obj and (not hasattr(obj, 'is_deleted') or not obj.is_deleted):
                        # Check condition if provided
                        if not rule.condition_callback or rule.condition_callback(obj):
                            active_related.append(obj)
                
                if active_related:
                    entity_names = [getattr(obj, 'name', str(getattr(obj, 'id', 'unknown'))) 
                                  for obj in active_related[:3]]  # Show first 3
                    more_count = len(active_related) - 3
                    entity_list = ', '.join(entity_names)
                    if more_count > 0:
                        entity_list += f" and {more_count} more"
                    
                    raise ValueError(
                        f"Cannot hard delete {self.__class__.__name__}: "
                        f"{len(active_related)} active {rule.relationship_name} records exist "
                        f"({entity_list}). Use force=True to override or handle dependencies first."
                    )
    
    def _handle_cascade_on_hard_delete(self, session: Session, deleted_by_user: str, force: bool):
        """Handle cascading when this record is hard deleted"""
        # Sort rules by cascade order to ensure proper deletion sequence
        sorted_rules = sorted(self._hard_delete_rules, key=lambda r: r.cascade_order)
        
        for rule in sorted_rules:
            try:
                self._process_hard_delete_cascade_rule(rule, session, deleted_by_user, force)
            except Exception as e:
                log_error(f"Error in hard delete cascade rule {rule.relationship_name} for {self.__class__.__name__}", 
                         exception=e)
                if not force:
                    raise
    
    def _process_hard_delete_cascade_rule(self, rule: HardDeleteCascadeRule, session: Session, 
                                        deleted_by_user: str, force: bool):
        """Process a single hard delete cascade rule"""
        related_objects = getattr(self, rule.relationship_name, None)
        if not related_objects:
            return
        
        # Handle single object vs collection
        if not isinstance(related_objects, list):
            related_objects = [related_objects]
        
        for related_obj in related_objects:
            if not related_obj:
                continue
                
            # Check condition if provided
            if rule.condition_callback and not rule.condition_callback(related_obj):
                continue
            
            # Apply cascading rule
            if rule.custom_handler:
                rule.custom_handler(related_obj, self, session, deleted_by_user, force)
            else:
                self._apply_hard_delete_cascade(rule, related_obj, session, deleted_by_user, force)
    
    def _apply_hard_delete_cascade(self, rule: HardDeleteCascadeRule, related_obj, 
                                 session: Session, deleted_by_user: str, force: bool):
        """Apply standard hard delete cascading rules"""
        if rule.cascade_type == HardDeleteCascadeRule.CASCADE_HARD_DELETE:
            if hasattr(related_obj, 'hard_delete'):
                related_obj.hard_delete(session, deleted_by_user, force)
            else:
                session.delete(related_obj)
                
        elif rule.cascade_type == HardDeleteCascadeRule.CASCADE_SOFT_DELETE:
            if hasattr(related_obj, 'soft_delete'):
                related_obj.soft_delete(deleted_by_user, session, cascade=True)
            else:
                log_error(f"Cannot soft delete {related_obj.__class__.__name__}: no soft_delete method")
                
        elif rule.cascade_type == HardDeleteCascadeRule.CASCADE_NULLIFY:
            # Find foreign key fields that reference this object and set them to null
            for column in related_obj.__table__.columns:
                if column.foreign_keys:
                    for fk in column.foreign_keys:
                        if fk.column.table == self.__table__:
                            setattr(related_obj, column.name, None)
                            log_info(f"Nullified {column.name} in {related_obj.__class__.__name__}")

    @classmethod
    def active_only(cls, query):
        """Filter query to only return available records (not deleted and not disabled)"""
        return query.filter(~cls.is_deleted).filter(~cls.is_disabled)
    
    @classmethod
    def available_only(cls, query):
        """Alias for active_only for clarity"""
        return cls.active_only(query)
    
    @classmethod
    def deleted_only(cls, query):
        """Filter query to only return deleted records"""
        return query.filter(cls.is_deleted)
    
    @classmethod
    def disabled_only(cls, query):
        """Filter query to only return disabled records"""
        return query.filter(cls.is_disabled)
    
    @classmethod
    def unavailable_only(cls, query):
        """Filter query to return deleted or disabled records"""
        return query.filter((cls.is_deleted) | (cls.is_disabled))

    def get_filtered_relationship(self, relationship_name: str, include_deleted=False, include_disabled=False):
        """Get relationship with soft delete filtering"""
        related_objects = getattr(self, relationship_name, None)
        if not related_objects:
            return self._get_empty_relationship_result(relationship_name)
        
        # Handle single object vs collection
        is_collection = isinstance(related_objects, list)
        if not is_collection:
            related_objects = [related_objects]
        
        filtered_objects = []
        for obj in related_objects:
            if self._should_include_object(obj, include_deleted, include_disabled):
                filtered_objects.append(obj)
        
        return self._format_relationship_result(filtered_objects, is_collection)

    def _get_empty_relationship_result(self, relationship_name: str):
        """Get the appropriate empty result for a relationship"""
        relationship_property = getattr(self.__class__, relationship_name).property
        is_collection = hasattr(relationship_property, 'collection_class')
        return [] if is_collection else None

    def _should_include_object(self, obj, include_deleted: bool, include_disabled: bool) -> bool:
        """Check if an object should be included based on its status"""
        if not obj:
            return False
            
        # Check if object has soft delete functionality
        if hasattr(obj, 'is_deleted') and hasattr(obj, 'is_disabled'):
            if obj.is_deleted and not include_deleted:
                return False
            if obj.is_disabled and not include_disabled:
                return False
        
        return True

    def _format_relationship_result(self, filtered_objects: List, is_collection: bool):
        """Format the relationship result based on whether it's a collection"""
        if is_collection:
            return filtered_objects
        else:
            return filtered_objects[0] if filtered_objects else None


# Helper function to set up cascade rules for models
def setup_cascade_rules(model_class, rules: List[SoftDeleteCascadeRule]):
    """Helper function to easily set up cascade rules for a model"""
    model_class._cascade_rules = rules


# Utility functions for common cascade patterns
def create_ingredient_cascade_rules():
    """Create standard cascade rules for ingredients"""
    return [
        SoftDeleteCascadeRule(
            "product_ingredients", 
            SoftDeleteCascadeRule.CASCADE_DISABLE,
            condition_callback=lambda pi: hasattr(pi, 'product') and pi.product
        )
    ]

def create_product_cascade_rules():
    """Create standard cascade rules for products"""
    return [
        SoftDeleteCascadeRule(
            "sales", 
            SoftDeleteCascadeRule.CASCADE_IGNORE  # Keep historical sales
        ),
        SoftDeleteCascadeRule(
            "pfand_history", 
            SoftDeleteCascadeRule.CASCADE_IGNORE  # Keep historical pfand records
        )
    ]

def create_user_cascade_rules():
    """Create standard cascade rules for users"""
    return [
        SoftDeleteCascadeRule(
            "sales", 
            SoftDeleteCascadeRule.CASCADE_IGNORE  # Keep sales history
        ),
        SoftDeleteCascadeRule(
            "donated_sales", 
            SoftDeleteCascadeRule.CASCADE_IGNORE  # Keep donation history
        ),
        SoftDeleteCascadeRule(
            "pfand_history", 
            SoftDeleteCascadeRule.CASCADE_IGNORE  # Keep pfand history
        )
    ]
