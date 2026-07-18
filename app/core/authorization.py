from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apis.auth_apis import get_current_user_id
from app.core.db.databases import async_get_db
from app.models.users import DepartmentEnum, RoleEnum, User

# 부서별 허용 & 역할별 허용
def require_permissions(
    allowed_departments: tuple[DepartmentEnum, ...] | None = None,
    allowed_roles: tuple[RoleEnum, ...] | None = None,
):
    async def checker(
        user_id: int = Depends(get_current_user_id),
        db: AsyncSession = Depends(async_get_db),
    ) -> User:
        result = await db.execute(
            select(User).where(
                User.id == user_id,
                User.is_active.is_(True),
            )
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증된 사용자를 찾을 수 없습니다.",
            )

        # ADMIN은 모든 API 허용
        if user.role == RoleEnum.ADMIN:
            return user

        if allowed_roles and user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="허용되지 않은 권한입니다.",
            )

        if (
            allowed_departments
            and user.department not in allowed_departments
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="허용되지 않은 부서입니다.",
            )

        return user

    return checker