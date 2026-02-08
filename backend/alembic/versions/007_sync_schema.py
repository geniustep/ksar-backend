"""Sync schema - مرجع للتغييرات المستقبلية

Revision ID: 007_sync_schema
Revises: 006_expand_access_code
Create Date: 2026-02-08

هذا الـ migration يربط السلسلة بعد 006. لا يغيّر الجداول.
لإضافة تغييرات جديدة: عدّل upgrade() ثم شغّل alembic upgrade head.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '007_sync_schema'
down_revision: Union[str, None] = '006_expand_access_code'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """لا تغيير في الجداول - السلسلة محدثة حتى 006."""
    pass


def downgrade() -> None:
    """لا تغيير."""
    pass
