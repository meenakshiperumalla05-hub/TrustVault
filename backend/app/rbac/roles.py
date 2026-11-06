
from fastapi import Depends, HTTPException, status

from app.models.user import User, UserRole
from app.routers.auth import get_current_user


def require_roles(*allowed_roles: UserRole):
    """
    Reusable dependency for role-based access control.
    """

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_user

    return role_checker


# Only administrators
admin_only = require_roles(UserRole.ADMIN)

# Document owners and administrators
owner_only = require_roles(
    UserRole.OWNER,
    UserRole.ADMIN,
)

# All authenticated roles
authenticated_users = require_roles(
    UserRole.ADMIN,
    UserRole.OWNER,
    UserRole.VIEWER,
)
