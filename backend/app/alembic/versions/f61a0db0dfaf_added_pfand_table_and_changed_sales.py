"""Added pfand_table and changed sales

Revision ID: f61a0db0dfaf
Revises: 7629d0c5f63a
Create Date: 2025-06-25 23:47:36.641862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f61a0db0dfaf'
down_revision: Union[str, Sequence[str], None] = '7629d0c5f63a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new consumer_id and donator_id columns
    op.add_column('sales', sa.Column('consumer_id', sa.Integer(), nullable=True))
    op.add_column('sales', sa.Column('donator_id', sa.Integer(), nullable=True))

    # Backfill consumer_id from old user_id
    op.execute("UPDATE sales SET consumer_id = user_id")

    # Now it's safe to drop user_id
    op.drop_constraint(None, 'sales', type_='foreignkey')
    op.drop_column('sales', 'user_id')

    # Create new FKs
    op.create_foreign_key(None, 'sales', 'users', ['consumer_id'], ['user_id'])
    op.create_foreign_key(None, 'sales', 'users', ['donator_id'], ['user_id'])

    op.create_table(
        'pfand_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id')),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.product_id')),
        sa.Column('counter', sa.Integer(), nullable=False, default=0)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Restore user_id column
    op.add_column('sales', sa.Column('user_id', sa.Integer(), nullable=True))

    # Backfill user_id from consumer_id
    op.execute("UPDATE sales SET user_id = consumer_id")

    # Drop foreign keys (use actual FK names or None if unsure)
    op.drop_constraint(None, 'sales', type_='foreignkey')  # consumer_id FK
    op.drop_constraint(None, 'sales', type_='foreignkey')  # donator_id FK

    # Restore FK for user_id
    op.create_foreign_key(None, 'sales', 'users', ['user_id'], ['user_id'])

    # Drop new columns
    op.drop_column('sales', 'donator_id')
    op.drop_column('sales', 'consumer_id')

    # Drop new table
    op.drop_table('pfand_history')
