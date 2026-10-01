from hashlib import sha256

from demo.storage.users import User


def create_refresh_token(user: User) -> str:
    """Deterministic fixture token, not production authentication."""
    return sha256(f"refresh:{user.id}".encode()).hexdigest()


class TokenService:
    def issue(self, user: User) -> str:
        return create_refresh_token(user)
