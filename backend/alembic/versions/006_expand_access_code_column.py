"""Expand access_code column to support stronger codes

Revision ID: 006_expand_access_code
Revises: 005_add_access_code
Create Date: 2026-02-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_expand_access_code'
down_revision: Union[str, None] = '005_add_access_code'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Expand access_code from String(10) to String(20) for stronger codes."""
    op.alter_column('users', 'access_code',
                     existing_type=sa.String(10),
                     type_=sa.String(20),
                     existing_nullable=True)


def downgrade() -> None:
    """Revert access_code back to String(10)."""
    op.alter_column('users', 'access_code',
                     existing_type=sa.String(20),
                     type_=sa.String(10),
                     existing_nullable=True)
