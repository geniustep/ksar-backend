"""Add access_code column to users table

Revision ID: 005_add_access_code
Revises: 004_superadmin_pending_phone
Create Date: 2026-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_add_access_code'
down_revision: Union[str, None] = '004_superadmin_pending_phone'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add access_code column to users table for storing plain text code."""
    op.add_column('users', sa.Column('access_code', sa.String(10), nullable=True))


def downgrade() -> None:
    """Remove access_code column."""
    op.drop_column('users', 'access_code')
