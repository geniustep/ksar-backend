"""Add audio_url and images columns to requests table

Revision ID: 001
Revises: 
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_add_audio_images'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add audio_url and images columns, and make description/address nullable."""
    # Add new columns
    op.add_column('requests', sa.Column('audio_url', sa.String(500), nullable=True))
    op.add_column('requests', sa.Column('images', sa.Text(), nullable=True))
    
    # Make description nullable (was required before)
    op.alter_column('requests', 'description',
                    existing_type=sa.Text(),
                    nullable=True)
    
    # Make address nullable (was required before)
    op.alter_column('requests', 'address',
                    existing_type=sa.String(500),
                    nullable=True)


def downgrade() -> None:
    """Revert the changes."""
    # Remove new columns
    op.drop_column('requests', 'images')
    op.drop_column('requests', 'audio_url')
    
    # Make description required again
    op.alter_column('requests', 'description',
                    existing_type=sa.Text(),
                    nullable=False)
    
    # Make address required again
    op.alter_column('requests', 'address',
                    existing_type=sa.String(500),
                    nullable=False)
