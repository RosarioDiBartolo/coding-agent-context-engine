"""Deliberately unmapped, outside the domain catalogue."""
from demo.auth.tokens import create_refresh_token
from demo.storage.users import User


def rotate_refresh_token(user_id: int) -> str:
    return create_refresh_token(User(user_id, "maintenance"))
