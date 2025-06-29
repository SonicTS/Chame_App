# soft_delete_mixin.py
# A mixin to add soft delete functionality to any model

from sqlalchemy import Column, Boolean, DateTime, String
from datetime import datetime, timezone

class SoftDeleteMixin:
    """Mixin to add soft delete functionality to models"""
    
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String, nullable=True)  # Track who deleted it
    
    def soft_delete(self, deleted_by_user=None):
        """Mark the record as deleted"""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by_user
    
    def restore(self):
        """Restore a soft-deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
    
    @classmethod
    def active_only(cls, query):
        """Filter query to only return non-deleted records"""
        return query.filter(~cls.is_deleted)
    
    @classmethod
    def deleted_only(cls, query):
        """Filter query to only return deleted records"""
        return query.filter(cls.is_deleted)
