from clerk_backend_api import (
    AuthenticateRequestOptions,
    authenticate_request,
)
from fastapi import HTTPException, Request

from backend.app.core.config import settings


# -----------------------------
# Current User
# -----------------------------

def get_current_user_id(
    request: Request,
) -> str:
    """
    Return the current authenticated user's ID.
    """

    # temporary mode for backend development before React auth is connected.
    if settings.use_test_auth:
        return "user_test_001"

    # Clerk verifies the session token sent by the frontend.
    auth_state = authenticate_request(
        request,
        AuthenticateRequestOptions(
            secret_key=settings.clerk_secret_key,
            accepts_token=["session_token"],
        ),
    )

    if not auth_state.is_signed_in:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    # "sub" contains the unique Clerk user ID.
    user_id = auth_state.payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
        )

    return user_id