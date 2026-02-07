"""OTP string columns (stub - already applied)

Revision ID: 003_otp_string_cols
Revises: 002_add_inspector_system
Create Date: 2026-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_otp_string_cols'
down_revision: Union[str, None] = '002_add_inspector_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Already applied - stub file to maintain chain."""
    pass


def downgrade() -> None:
    """Already applied - stub file to maintain chain."""
    pass
