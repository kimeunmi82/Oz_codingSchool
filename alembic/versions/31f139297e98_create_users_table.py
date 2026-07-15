"""Create users table

Revision ID: 31f139297e98
Revises: 67ce7c5af502
Create Date: 2026-07-15 20:48:56.887655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31f139297e98'
down_revision: Union[str, Sequence[str], None] = '67ce7c5af502'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


gender_enum = sa.Enum("M", "F", name="gender")
department_enum = sa.Enum("MEDICAL", "DEV", "RESEARCH", name="department")
role_enum = sa.Enum("PENDING", "STAFF", "ADMIN", name="role")


def upgrade() -> None:
    bind = op.get_bind()
    gender_enum.create(bind, checkfirst=True)
    department_enum.create(bind, checkfirst=True)
    role_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=255), nullable=True, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=20), nullable=True),
        sa.Column("phone_number", sa.String(length=20), nullable=True, unique=True),
        sa.Column("gender", gender_enum, nullable=False, comment="성별 선택"),
        sa.Column("department", department_enum, nullable=False, comment="부서 선택"),
        sa.Column("role", role_enum, nullable=False, comment="부여된 역할 권한"),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="계정 활성화 여부",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            comment="유저 생성 일시",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            comment="유저 정보 수정 일시",
        ),
    )


def downgrade() -> None:
    op.drop_table("users")

    bind = op.get_bind()
    role_enum.drop(bind, checkfirst=True)
    department_enum.drop(bind, checkfirst=True)
    gender_enum.drop(bind, checkfirst=True)