import unittest
from demo.api.session import login
from demo.auth.tokens import TokenService, create_refresh_token
from demo.storage.users import User


class SessionTests(unittest.TestCase):
    def test_login(self):
        self.assertEqual(login(7)["refresh_token"], create_refresh_token(User(7, "Ada")))

    def test_service(self):
        user = User(8, "Grace")
        self.assertEqual(TokenService().issue(user), create_refresh_token(user))
