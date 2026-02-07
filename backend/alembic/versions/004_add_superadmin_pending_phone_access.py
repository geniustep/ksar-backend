"""Add superadmin role, pending user status, and phone access control

Revision ID: 004_superadmin_pending_phone
Revises: 003_otp_string_cols
Create Date: 2026-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_superadmin_pending_phone'
down_revision: Union[str, None] = '003_otp_string_cols'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add superadmin role, pending user status, and allow_phone_access to assignments."""
    
    # 1. Add SUPERADMIN to userrole enum
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'SUPERADMIN'")
    
    # 2. Add PENDING to userstatus enum
    op.execute("ALTER TYPE userstatus ADD VALUE IF NOT EXISTS 'PENDING'")
    
    # 3. Add allow_phone_access column to assignments table
    op.add_column('assignments', sa.Column('allow_phone_access', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Revert changes."""
    
    # Remove allow_phone_access column
    op.drop_column('assignments', 'allow_phone_access')
    
    # Note: PostgreSQL doesn't support removing values from enums easily.
    # The enum values (SUPERADMIN, PENDING) will remain but won't be used.
