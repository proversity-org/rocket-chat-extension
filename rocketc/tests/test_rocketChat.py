import unittest
import hashlib
from mock import MagicMock, patch
from rocketc.rocketc import RocketChatXBlock


class TestRocketChat(unittest.TestCase):
    """ Unit tests for RocketChat Xblock"""

    def setUp(self):
        """Set up general variables"""

        self.runtime_mock = MagicMock()
        scope_ids_mock = MagicMock()
        scope_ids_mock.usage_id = u'0'
        self.block = RocketChatXBlock(
            self.runtime_mock, scope_ids=scope_ids_mock)
        self.block.email = "email"

    @patch('rocketc.rocketc.RocketChatXBlock.admin_data')
    def test_request_rocket_chat(self, mock_response):
        """Test for the request rocket chat method """
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
            data_post = self.block._request_rocket_chat("post", "users.create")

        with patch('rocketc.rocketc.requests.get') as mock_get:
            mock_get.return_value.json.return_value = info
            data_get = self.block._request_rocket_chat("get", "info")

        self.assertEqual(data_post, users)
        self.assertEqual(data_get, info)

    @patch('rocketc.rocketc.RocketChatXBlock._update_user')
    @patch('rocketc.rocketc.RocketChatXBlock.create_token')
    def test_login(self, mock_token, mock_update_user):
        """Test for the login method"""

        test_data = {"username": "test_user_name",
                "anonymous_student_id": "test_anonymous_student_id",
                "email": "test_email",
                "course": "test_course",
                "role": "test_role"
            }

        mock_token.return_value = {'success': True}
        success = {'success': True}
        with patch('rocketc.rocketc.RocketChatXBlock.search_rocket_chat_user', return_value=success):
            result_if = self.block.login(test_data)
            mock_token.assert_called_with(test_data['username'])

        success['success'] = False
        with patch('rocketc.rocketc.RocketChatXBlock.search_rocket_chat_user', return_value=success):
            with patch('rocketc.rocketc.RocketChatXBlock.create_user'):
                result_else = self.block.login(test_data)
                mock_token.assert_called_with(test_data['username'])


        self.assertTrue(result_if['success'])
        self.assertTrue(result_else['success'])

    @patch('rocketc.rocketc.RocketChatXBlock._request_rocket_chat')
    def test_search_rocket_chat_user(self, mock_request):
        """Test for the search user method"""
        method = "get"
        success = {'success': True}
        username = "test_user_name"
        mock_request.return_value = success
        url_path = "{}?{}={}".format("users.info", "username", username)

        response = self.block.search_rocket_chat_user(username)

        mock_request.assert_called_with(method, url_path)
        self.assertTrue(response['success'])

    @patch('rocketc.rocketc.RocketChatXBlock._request_rocket_chat')
    def test_search_rocket_chat_group(self, mock_request):
        """Test for the search group method"""
        method = "get"
        success = {'success': True}
        room_name = "test_room_name"
        mock_request.return_value = success
        url_path = "{}?{}={}".format("groups.info", "roomName", room_name)

        response = self.block._search_rocket_chat_group(room_name)

        mock_request.assert_called_with(method, url_path)
        self.assertTrue(response['success'])

    @patch('rocketc.rocketc.RocketChatXBlock._request_rocket_chat')
    def test_create_user(self, mock_request):
        """Test for the create user method"""
        method = "post"
        success = {'success': True}

        email = "test_email"
        username = "test_user_name"
        name = "test_name"
        salt = "HarryPotter_and_thePrisoner_of _Azkaban"

        mock_request.return_value = success
        url_path = "users.create"

        password = "{}{}".format(name, salt)
        password = hashlib.sha1(password).hexdigest()
        data = {"name": name, "email": email,
                "password": password, "username": username}

        response = self.block.create_user(name, email, username)

        mock_request.assert_called_with(method, url_path, data)
        self.assertTrue(response['success'])

    @patch('rocketc.rocketc.RocketChatXBlock._request_rocket_chat')
    def test_create_token(self, mock_request):
        """Test for the create token method"""
        method = "post"
        success = {'success': True}

        username = "test_user_name"

        mock_request.return_value = success
        url_path = "users.createToken"

        data = {'username': username}

        response = self.block.create_token(username)

        mock_request.assert_called_with(method, url_path, data)
        self.assertTrue(response['success'])

    @patch('rocketc.rocketc.RocketChatXBlock._request_rocket_chat')
    def test_create_group(self, mock_request):
        """Test for the create group method"""
        method = "post"
        success = {'success': True}

        name = "test_name"

        mock_request.return_value = success
        url_path = "groups.create"

        data = {'name': name}

        response = self.block._create_group(name)
        self.assertEquals(response, success)
        mock_request.assert_called_with(method, url_path, data)

    @patch('rocketc.rocketc.RocketChatXBlock._add_to_group')
    def test_add_to_course_group(self, mock_add_to_group):
        """Test for the add course group method"""
        group_name = "test_group"
        user_id = "test_user_id"
        data = {'success': True, 'group': {'_id': "test_group_id"}}
        with patch('rocketc.rocketc.RocketChatXBlock._search_rocket_chat_group', return_value=data):
            self.block.add_to_course_group(group_name, user_id)
            mock_add_to_group.assert_called_with(user_id, data['group']['_id'])

        data['success'] = False
        with patch('rocketc.rocketc.RocketChatXBlock._search_rocket_chat_group', return_value=data):
            with patch('rocketc.rocketc.RocketChatXBlock._create_group', return_value=data):
                self.block.add_to_course_group(group_name, user_id)
                mock_add_to_group.assert_called_with(user_id, data['group']['_id'])

    @patch('rocketc.rocketc.RocketChatXBlock._request_rocket_chat')
    def test_add_to_group(self, mock_request):
        """Test for the add group method"""
        method = "post"
        success = {'success': True}

        user_id = "test_user_id"
        room_id = "test_room_id"

        mock_request.return_value = success
        url_path = "groups.invite"

        data = {"roomId": room_id, "userId": user_id}

        response = self.block._add_to_group(user_id, room_id)
        mock_request.assert_called_with(method, url_path, data)
        self.assertTrue(response['success'])

    @patch('rocketc.rocketc.RocketChatXBlock._request_rocket_chat')
    def test_change_role(self, mock_request):
        """Test for chage role method"""
        method = "post"
        success = {'success': True}

        user_id = "test_user_id"
        role = "test_role"

        mock_request.return_value = success
        url_path = "users.update"

        data = {"userId": user_id, "data": {"roles": [role]}}

        self.block.change_role(user_id, role)
        mock_request.assert_called_with(method, url_path, data)

    @patch('rocketc.rocketc.RocketChatXBlock._user_image_url')
    @patch('rocketc.rocketc.RocketChatXBlock._request_rocket_chat')
    def test_set_avatar(self, mock_request, mock_user_image_url):
        """Test the method for set the avatar in RocketChat"""
        method = "post"
        username = "test_user_name"
        url ="test_url"

        mock_user_image_url.return_value = url
        url_path = "users.setAvatar"

        data = {"username": username, "avatarUrl": url}
        self.block._set_avatar(username)
        mock_request.assert_called_with(method, url_path, data)

    @patch('rocketc.rocketc.RocketChatXBlock._request_rocket_chat')
    def test_update_user(self, mock_request):
        """Test the metho to update the profile user"""
        method = "post"
        success = {'success': True}

        user_id = "test_user_id"
        username = "test_user_name"
        email = "test_email"

        mock_request.return_value = success
        url_path = "users.update"

        data = {"userId": user_id, "data": {"email": email }}

        with patch('rocketc.rocketc.RocketChatXBlock._set_avatar'):
            self.block._update_user(user_id, username, email)

        self.assertEqual(self.block.email, email)
        mock_request.assert_called_with(method, url_path, data)
