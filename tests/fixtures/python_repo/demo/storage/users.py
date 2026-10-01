from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    name: str


def get_user(user_id: int) -> User:
    return User(user_id, "Ada")
