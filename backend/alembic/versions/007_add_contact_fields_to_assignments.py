"""Add contact fields to assignments table

Revision ID: 007_add_contact_fields
Revises: 006_expand_access_code
Create Date: 2026-02-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007_add_contact_fields'
down_revision: Union[str, None] = '007_sync_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add contact_name, contact_phone, inspector_phone to assignments."""
    op.add_column('assignments', sa.Column('contact_name', sa.String(200), nullable=True))
    op.add_column('assignments', sa.Column('contact_phone', sa.String(20), nullable=True))
    op.add_column('assignments', sa.Column('inspector_phone', sa.String(20), nullable=True))


def downgrade() -> None:
    """Remove contact fields."""
    op.drop_column('assignments', 'inspector_phone')
    op.drop_column('assignments', 'contact_phone')
    op.drop_column('assignments', 'contact_name')
