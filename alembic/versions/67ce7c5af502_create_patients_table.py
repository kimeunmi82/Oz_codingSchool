"""Create patients table

Revision ID: 67ce7c5af502
Revises: 
Create Date: 2026-07-15 20:48:29.106083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67ce7c5af502'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


gender_enum = sa.Enum("M", "F", name="gender")


def upgrade() -> None:
    bind = op.get_bind()
    gender_enum.create(bind, checkfirst=True)

    op.create_table(
        "patients",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=30), nullable=False, comment="환자 성명"),
        sa.Column("age", sa.SmallInteger(), nullable=False, comment="smallint"),
        sa.Column("gender", gender_enum, nullable=True, comment="환자 성별"),
        sa.Column(
            "phone",
            sa.String(length=11),
            nullable=False,
            comment="환자 연락처, 국내 전화번호로 한정",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            comment="환자 정보 등록 일시",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            comment="환자 정보 수정 일시",
        ),
    )


def downgrade() -> None:
    op.drop_table("patients")

    bind = op.get_bind()
    gender_enum.drop(bind, checkfirst=True)