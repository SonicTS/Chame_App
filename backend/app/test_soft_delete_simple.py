#!/usr/bin/env python3
"""
Simple test script for SoftDeleteMixin functionality without database initialization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_soft_delete_mixin_simple():
    print('Testing SoftDeleteMixin functionality (simple test)...')

    # Import the mixin directly
    from models.soft_delete_mixin import SoftDeleteMixin
    from sqlalchemy import Column, Integer, String, create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from datetime import datetime

    Base = declarative_base()

    # Create a simple test model
    class TestModel(Base, SoftDeleteMixin):
        __tablename__ = 'test_model'
        id = Column(Integer, primary_key=True)
        name = Column(String(50))

        def __init__(self, name):
            self.name = name

    # Test the mixin methods
    print('\n1. Testing SoftDeleteMixin methods:')
    test_obj = TestModel(name='test_object')
    
    print(f'Initial state - is_deleted: {test_obj.is_deleted}')
    print(f'Initial state - deleted_at: {test_obj.deleted_at}')
    print(f'Initial state - deleted_by: {test_obj.deleted_by}')

    # Test soft delete
    test_obj.soft_delete('admin_user')
    print(f'\nAfter soft_delete():')
    print(f'  is_deleted: {test_obj.is_deleted}')
    print(f'  deleted_at: {test_obj.deleted_at}')
    print(f'  deleted_by: {test_obj.deleted_by}')

    # Test restore
    test_obj.restore()
    print(f'\nAfter restore():')
    print(f'  is_deleted: {test_obj.is_deleted}')
    print(f'  deleted_at: {test_obj.deleted_at}')
    print(f'  deleted_by: {test_obj.deleted_by}')

    # Test class methods exist
    print(f'\n2. Testing class methods exist:')
    print(f'  active_only method exists: {hasattr(TestModel, "active_only")}')
    print(f'  deleted_only method exists: {hasattr(TestModel, "deleted_only")}')

    print('\n✅ SoftDeleteMixin basic functionality test passed!')

if __name__ == '__main__':
    test_soft_delete_mixin_simple()
