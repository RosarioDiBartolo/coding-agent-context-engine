from demo.auth.tokens import create_refresh_token
from demo.storage.users import get_user


def login(user_id: int) -> dict[str, str]:
    return {"refresh_token": create_refresh_token(get_user(user_id))}
