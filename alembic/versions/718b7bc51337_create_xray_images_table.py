"""Create xray images table

Revision ID: 718b7bc51337
Revises: 021f0b7ed848
Create Date: 2026-07-15 21:53:02.268882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '718b7bc51337'
down_revision: Union[str, Sequence[str], None] = '021f0b7ed848'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "xray_images",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "record_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "uploader_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "image_url",
            sa.String(length=2048),
            nullable=False,
        ),
        sa.Column(
            "shooting_datetime",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["record_id"],
            ["medical_records.id"],
        ),
        sa.ForeignKeyConstraint(
            ["uploader_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_xray_images_record_id"),
        "xray_images",
        ["record_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_xray_images_uploader_id"),
        "xray_images",
        ["uploader_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_xray_images_uploader_id"),
        table_name="xray_images",
    )

    op.drop_index(
        op.f("ix_xray_images_record_id"),
        table_name="xray_images",
    )

    op.drop_table("xray_images") 
