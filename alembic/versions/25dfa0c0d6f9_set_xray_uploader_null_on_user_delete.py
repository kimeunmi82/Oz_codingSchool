"""set xray uploader null on user delete

Revision ID: 25dfa0c0d6f9
Revises: bb4ed704adb3
Create Date: 2026-07-21 18:44:54.257481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '25dfa0c0d6f9'
down_revision: Union[str, Sequence[str], None] = 'bb4ed704adb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """회원 삭제 시 X-ray 업로더 연결을 NULL로 변경합니다."""

    op.alter_column(
        "xray_images",
        "uploader_id",
        existing_type=mysql.INTEGER(),
        nullable=True,
    )

    op.drop_constraint(
        "xray_images_ibfk_2",
        "xray_images",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "fk_xray_images_uploader_id_users",
        "xray_images",
        "users",
        ["uploader_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """기존 필수 업로더 외래키로 되돌립니다."""

    op.drop_constraint(
        "fk_xray_images_uploader_id_users",
        "xray_images",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "xray_images_ibfk_2",
        "xray_images",
        "users",
        ["uploader_id"],
        ["id"],
    )

    op.alter_column(
        "xray_images",
        "uploader_id",
        existing_type=mysql.INTEGER(),
        nullable=False,
    )