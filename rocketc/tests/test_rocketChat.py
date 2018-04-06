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
        self.block.user_data = MagicMock({"username": "test_user_name"})

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
            "info": {
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

    # Mock create token method
    @patch('rocketc.rocketc.RocketChatXBlock.create_token')
    def test_login(self, mock_token):
        """"""
        mock_token.return_value = {'success': True}
        success = {'success': True}
        with patch('rocketc.rocketc.RocketChatXBlock.search_rocket_chat_user', return_value=success):
            result_if = self.block.login(self.block.user_data)
            mock_token.assert_called_with(self.block.user_data['username'])

        success['success'] = False
        with patch('rocketc.rocketc.RocketChatXBlock.search_rocket_chat_user', return_value=success):
            with patch('rocketc.rocketc.RocketChatXBlock.create_user'):
                result_else = self.block.login(self.block.user_data)
                mock_token.assert_called_with(self.block.user_data['username'])

        self.assertTrue(result_if['success'])
        self.assertTrue(result_else['success'])

    @patch('rocketc.rocketc.RocketChatXBlock.request_rocket_chat')
    def test_search_rocket_chat_user(self, mock_request):
        """"""
        method = "get"
        success = {'success': True}
        username = self.block.user_data['username']
        mock_request.return_value = success
        url_path = "{}?{}={}".format("users.info", "username", username)

        response = self.block.search_rocket_chat_user(username)

        mock_request.assert_called_with(method, url_path)
        self.assertTrue(response['success'])

    @patch('rocketc.rocketc.RocketChatXBlock.request_rocket_chat')
    def test_search_rocket_chat_group(self, mock_request):
        """"""
        method = "get"
        success = {'success': True}
        room_name = "test_room_name"
        mock_request.return_value = success
        url_path = "{}?{}={}".format("groups.info", "roomName", room_name)

        response = self.block.search_rocket_chat_group(room_name)

        mock_request.assert_called_with(method, url_path)
        self.assertTrue(response['success'])
