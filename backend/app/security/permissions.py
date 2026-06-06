from fastapi import Depends, HTTPException, status

from app.models.enums import UserRole
from app.models.user import User
from app.security.dependencies import get_current_user


def require_role(*allowed_roles: UserRole):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return checker
