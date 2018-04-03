import unittest
from mock import patch
from rocketc.rocketc import RocketChatXBlock

class TestRocketChat(unittest.TestCase):
    """ Unit tests for RocketChat Xblock"""
    def setUp(self):
        """"""
        self.admin_data["auth_token"] = ""
        self.admin_data["user_id"] = ""
    

    def test_request_rocket_chat(self):
        """"""
        users = [{
            "id": 0,
            "first_name": "Dell",
            "last_name": "Norval",
            "phone": "994-979-3976"
        }]

        with patch('rocketc.requests.post') as mock_post:
            mock_post.return_value.json.return_value = users
            data = RocketChatXBlock.request_rocket_chat("post", "users.create")

        self.assertEqual(data, users)
