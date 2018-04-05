import unittest
from mock import MagicMock, patch
from rocketc.rocketc import RocketChatXBlock

class TestRocketChat(unittest.TestCase):
    """ Unit tests for RocketChat Xblock"""

    def setUp(self):
        """"""
        self.runtime_mock = MagicMock()
        scope_ids_mock = MagicMock()
        scope_ids_mock.usage_id = u'0'
        self.block = RocketChatXBlock(
            self.runtime_mock, scope_ids=scope_ids_mock)
        self.block.admin_data = MagicMock()
        self.block.user_data = MagicMock()

    def test_request_rocket_chat(self):
        """"""
        users = [{
            "user": {
                "_id": "BsNr28znDkG8aeo7W",
                "createdAt": "2016-09-13T14:57:56.037Z",
                },
            "success": "true",
        }]

        info = [{
            "success": "true",
            "info":{
                "version": "0.47.0-develop"
            }
        }]

        with patch('rocketc.rocketc.requests.post') as mock_post:
            mock_post.return_value.json.return_value = users
            data_post = self.block.request_rocket_chat("post", "users.create")

        with patch('rocketc.rocketc.requests.get') as mock_get:
            mock_get.return_value.json.return_value = info
            data_get = self.block.request_rocket_chat("get", "info")

        self.assertEqual(data_post, users)
        self.assertEqual(data_get, info)

    @patch('rocketc.rocketc.create_token') # Mock create token method
    def test_login(self, mock_token):
        """"""
        mock_token.return_value = {'success': True}
        success = {'success': True}
        with patch('rocketc.rocketc.search_rocket_chat_user') as mock_search:
            mock_search.return_value = success
            data = self.block.login(self.block.user_data)
        self.assertTrue(data['success'])