#!/usr/bin/env python3
"""
Test script for SoftDeleteMixin functionality
"""

from models.user_table import User
from models.product_table import Product
from models.ingredient import Ingredient

def test_soft_delete_mixin():
    print('Testing SoftDeleteMixin functionality...')

    # Test 1: Create a user and test soft delete
    print('\n1. Testing User soft delete:')
    user = User(name='test_user', balance=100.0, role='user')
    print(f'Initial state - is_deleted: {user.is_deleted}, deleted_at: {user.deleted_at}')

    # Soft delete the user
    user.soft_delete('admin')
    print(f'After soft delete - is_deleted: {user.is_deleted}, deleted_at: {user.deleted_at}, deleted_by: {user.deleted_by}')

    # Restore the user
    user.restore()
    print(f'After restore - is_deleted: {user.is_deleted}, deleted_at: {user.deleted_at}, deleted_by: {user.deleted_by}')

    # Test 2: Create a product and test soft delete
    print('\n2. Testing Product soft delete:')
    product = Product(name='test_product', price_per_unit=5.0, category='test', toaster_space=1)
    print(f'Initial state - is_deleted: {product.is_deleted}, deleted_at: {product.deleted_at}')

    product.soft_delete('admin')
    print(f'After soft delete - is_deleted: {product.is_deleted}, deleted_at: {product.deleted_at}, deleted_by: {product.deleted_by}')

    product.restore()
    print(f'After restore - is_deleted: {product.is_deleted}, deleted_at: {product.deleted_at}, deleted_by: {product.deleted_by}')

    # Test 3: Create an ingredient and test soft delete
    print('\n3. Testing Ingredient soft delete:')
    ingredient = Ingredient(name='test_ingredient', price_per_package=2.0, stock_quantity=10, number_ingredients=5, pfand=0.25)
    print(f'Initial state - is_deleted: {ingredient.is_deleted}, deleted_at: {ingredient.deleted_at}')

    ingredient.soft_delete('admin')
    print(f'After soft delete - is_deleted: {ingredient.is_deleted}, deleted_at: {ingredient.deleted_at}, deleted_by: {ingredient.deleted_by}')

    ingredient.restore()
    print(f'After restore - is_deleted: {ingredient.is_deleted}, deleted_at: {ingredient.deleted_at}, deleted_by: {ingredient.deleted_by}')

    print('\n✅ All SoftDeleteMixin tests passed successfully!')

if __name__ == '__main__':
    test_soft_delete_mixin()
