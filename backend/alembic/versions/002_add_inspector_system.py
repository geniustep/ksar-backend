"""Add inspector role, pending/rejected status, and inspector fields to requests

Revision ID: 002
Revises: 001_add_audio_images
Create Date: 2026-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '002_add_inspector_system'
down_revision: Union[str, None] = '001_add_audio_images'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add inspector system: new role, new statuses, new columns."""
    
    # 1. Add INSPECTOR to userrole enum
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'inspector'")
    
    # 2. Add PENDING and REJECTED to requeststatus enum
    op.execute("ALTER TYPE requeststatus ADD VALUE IF NOT EXISTS 'pending' BEFORE 'new'")
    op.execute("ALTER TYPE requeststatus ADD VALUE IF NOT EXISTS 'rejected' AFTER 'cancelled'")
    
    # 3. Add inspector_id and inspector_notes columns to requests table
    op.add_column('requests', sa.Column('inspector_id', UUID(as_uuid=True), nullable=True))
    op.add_column('requests', sa.Column('inspector_notes', sa.Text(), nullable=True))
    
    # 4. Add foreign key and index for inspector_id
    op.create_foreign_key(
        'fk_requests_inspector_id',
        'requests', 'users',
        ['inspector_id'], ['id'],
    )
    op.create_index('ix_requests_inspector_id', 'requests', ['inspector_id'])
    
    # 5. Update existing requests from 'new' default to keep them as 'new'
    # (existing requests should stay as 'new', only new ones will be 'pending')


def downgrade() -> None:
    """Revert inspector system changes."""
    
    # Remove index and foreign key
    op.drop_index('ix_requests_inspector_id', table_name='requests')
    op.drop_constraint('fk_requests_inspector_id', 'requests', type_='foreignkey')
    
    # Remove columns
    op.drop_column('requests', 'inspector_notes')
    op.drop_column('requests', 'inspector_id')
    
    # Note: PostgreSQL doesn't support removing values from enums easily.
    # The enum values (inspector, pending, rejected) will remain but won't be used.
