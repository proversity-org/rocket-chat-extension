import unittest
import hashlib
import json

from django.test.utils import override_settings
from mock import MagicMock, patch, PropertyMock
from rocketc.rocketc import RocketChatXBlock
from rocketc.api_rocket_chat import ApiRocketChat
from rocketc.api_teams import ApiTeams


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

        self.modules = {
            'rocketc.openedx_dependencies': MagicMock(),
        }

        self.module_patcher = patch.dict('sys.modules', self.modules)
        self.module_patcher.start()

    @patch('rocketc.rocketc.RocketChatXBlock.api_rocket_chat')
    def test_add_user_to_course_group(self, mock_api_rocket):
        """Test for the add course group method"""
        group_name = "test_group"
        user_id = "test_user_id"
        data = {'success': True, 'group': {'_id': "test_group_id"}}

        mock_api_rocket.search_rocket_chat_group.return_value = data
        self.block._add_user_to_course_group(group_name, user_id)
        mock_api_rocket.add_user_to_group.assert_called_with(
            user_id, data['group']['_id'])

        with patch('rocketc.rocketc.RocketChatXBlock.user_data', new_callable=PropertyMock) as mock_user:
            mock_user.return_value = {"username": "test_user_name"}
            data['success'] = False
            mock_api_rocket.search_rocket_chat_group.return_value = data
            self.block._add_user_to_course_group(group_name, user_id)
            mock_api_rocket.create_group.assert_called_with(
                group_name, "test_user_name")

    @patch('rocketc.rocketc.RocketChatXBlock.api_rocket_chat')
    def test_add_user_to_default_group(self, mock_api_rocket):
        """
        Test the method add to default group
        """
        group_name = "test_group_name"
        user_id = "test_user_id"

        mock_api_rocket.search_rocket_chat_group.return_value = {
            "success": True, "group": {"_id": "1234"}}

        self.assertTrue(
            self.block._add_user_to_default_group(group_name, user_id))
        mock_api_rocket.add_user_to_group.assert_called_with(user_id, "1234")

        mock_api_rocket.search_rocket_chat_group.return_value = {
            "success": False}

        self.assertFalse(
            self.block._add_user_to_default_group(group_name, user_id))
        mock_api_rocket.add_user_to_group.assert_called_with(user_id, "1234")

    @patch('rocketc.rocketc.RocketChatXBlock._get_team')
    @patch('rocketc.rocketc.RocketChatXBlock.api_rocket_chat')
    def test_add_user_to_team_group(self, mock_api_rocket, mock_get_team):
        """
        test method add to team group
        """
        user_id = "test_user_id"
        username = "test_user_name"
        course_id = "test_course_id"

        mock_get_team.return_value = None

        self.assertFalse(self.block._add_user_to_team_group(
            user_id, username, course_id))

        mock_get_team.return_value = {"name": "name", "topic_id": "test"}
        mock_api_rocket.search_rocket_chat_group.return_value = {
            "success": True, "group": {"_id": "1234"}}

        self.block._add_user_to_team_group(user_id, username, course_id)
        self.assertEqual(self.block.team_channel, "Team-test-name")

        mock_api_rocket.add_user_to_group.assert_called_with(user_id, "1234")

        mock_api_rocket.search_rocket_chat_group.return_value = {
            "success": False}
        self.block._add_user_to_team_group(user_id, username, course_id)

        mock_api_rocket.create_group.assert_called_with(
            "Team-test-name", username)

    @patch('rocketc.rocketc.RocketChatXBlock._teams_is_enabled')
    def test_channels_enabled(self, mock_team):
        """
        Test the method channels is enabled
        """
        output = ["Main View", "Team Discussion", "Specific Channel"]
        mock_team.return_value = True
        self.assertEqual(self.block.channels_enabled(), output)

        output = ["Main View", "Specific Channel"]
        mock_team.return_value = False
        self.assertEqual(self.block.channels_enabled(), output)

    @patch('rocketc.rocketc.RocketChatXBlock.api_rocket_chat')
    def test_create_group(self, mock_api_rocket):
        """test create group"""

        data = {"groupName": "", "description": "test:description",
                "topic": "test_topic"}

        mock_request = MagicMock(method="POST", body=json.dumps(data))

        result = self.block.create_group(mock_request)

        self.assertEqual(json.loads(result.body)[
                         "error"], "Group Name is not valid")

        data = {"groupName": "test_group",
                "description": "test:description", "topic": "test_topic"}

        mock_request = MagicMock(method="POST", body=json.dumps(data))
        mock_api_rocket.create_group.return_value = {
            "success": True, "group": {"_id": "1234"}}

        result = self.block.create_group(mock_request)

        mock_api_rocket.create_group.assert_called_with(data["groupName"])
        self.assertEqual(self.block.default_channel, data["groupName"])
        self.assertEqual(json.loads(result.body), {
                         "success": True, "group": {"_id": "1234"}})

    @patch('rocketc.rocketc.RocketChatXBlock.api_rocket_chat')
    @patch('rocketc.rocketc.RocketChatXBlock._update_user')
    @patch('rocketc.rocketc.RocketChatXBlock._join_user_to_groups')
    @patch('rocketc.rocketc.RocketChatXBlock.login')
    def test_init(self, mock_login, mock_join_user, mock_update_user, mock_api_rocket):
        """
        Test the method to initialize the xblock
        """
        with patch('rocketc.rocketc.RocketChatXBlock.user_data', new_callable=PropertyMock) as mock_user_data:
            user_data = {"role": "instructor"}
            mock_user_data.return_value = user_data
            user_id = "test_user_id"
            data = {"userId": user_id}
            response_login = {"success": True, "data": data}
            mock_login.return_value = response_login
            self.block.rocket_chat_role = "user"

            self.assertEqual(self.block.init(), data)
            mock_join_user.assert_called_with(user_id, user_data)
            mock_update_user.assert_called_with(user_id, user_data)
            mock_api_rocket.change_user_role.assert_called_with(user_id, "bot")

            mock_login.return_value = {
                "success": False, "errorType": "test_error"}

            self.assertEqual(self.block.init(), "test_error")

    @patch('rocketc.rocketc.RocketChatXBlock.api_rocket_chat')
    def test_login(self, mock_api_rocket):
        """Test for the login method"""

        test_data = {"username": "test_user_name",
                     "anonymous_student_id": "test_anonymous_student_id",
                     "email": "test_email",
                     "course": "test_course",
                     "role": "test_role"
                     }
        mock_api_rocket.create_token.return_value = {'success': True}
        success = {'success': True}

        result_if = self.block.login(test_data)
        mock_api_rocket.create_token.assert_called_with(test_data['username'])

        success['success'] = False

        mock_api_rocket.search_rocket_chat_user.return_value = success

        result_else = self.block.login(test_data)
        mock_api_rocket.create_user.assert_called_with(test_data["anonymous_student_id"], test_data[
            "email"], test_data["username"])
        mock_api_rocket.create_token.assert_called_with(test_data['username'])

        self.assertTrue(result_if['success'])
        self.assertTrue(result_else['success'])

    @override_settings(LMS_ROOT_URL="http://127.0.0.1")
    @patch('rocketc.rocketc.ApiTeams')
    def test_get_team(self, mock_teams):
        """
        This method gets the user's team
        """
        username = "test_user_name"
        course_id = " test_course_id"
        mock_teams.return_value.get_user_team.return_value = ["test_team"]

        with patch('rocketc.rocketc.RocketChatXBlock.xblock_settings', new_callable=PropertyMock) as mock_settings:
            mock_settings.return_value = {"username": "test_user_name", "password": "test_password",
                                          "client_id": "test_id", "client_secret": "test_secret"}
            self.assertEqual(self.block._get_team(
                username, course_id), "test_team")
            mock_teams.return_value.get_user_team.return_value = []
            self.assertIsNone(self.block._get_team(username, course_id))

    def test_join_user_to_groups(self):
        """
        Test the method join groups
        """

        user_id = "test_user_id"
        user_data = {"course_id": "test_course_id",
                     "username": "test_user_name", "course": "test_course"}
        self.block.default_channel = "test_default_channel"
        self.block.selected_view = "Team Discussion"

        with patch('rocketc.rocketc.RocketChatXBlock._teams_is_enabled', return_value=True):
            with patch('rocketc.rocketc.RocketChatXBlock._add_user_to_team_group', return_value=True):
                self.block._join_user_to_groups(user_id, user_data)
                self.assertTrue(self.block.ui_is_block)

        self.block.selected_view = "Specific Channel"

        with patch('rocketc.rocketc.RocketChatXBlock._add_user_to_default_group', return_value=True):
            self.block._join_user_to_groups(user_id, user_data)
            self.assertTrue(self.block.ui_is_block)

        self.block.selected_view = ""

        with patch('rocketc.rocketc.RocketChatXBlock._add_user_to_course_group'):
            self.block._join_user_to_groups(user_id, user_data)
            self.assertFalse(self.block.ui_is_block)

    @patch('rocketc.rocketc.RocketChatXBlock._user_image_url')
    @patch('rocketc.rocketc.RocketChatXBlock.api_rocket_chat')
    def test_update_user(self, mock_api_rocket, mock_url):
        """Test update user """
        user_data = {"email": "test_email", "username": "test_user_name"}
        user_id = "test_user_id"

        mock_url.return_value = "test_url"

        self.block._update_user(user_id, user_data)
        mock_api_rocket.update_user.assert_called_with(
            user_id, user_data["email"])
        mock_api_rocket.set_avatar.assert_called_with(
            user_data["username"], "test_url")

    @override_settings(LMS_ROOT_URL="http://127.0.0.1/")
    @patch('rocketc.rocketc.User')
    @patch('rocketc.rocketc.RocketChatXBlock.user_data')
    def test_user_image_url(self, mock_user_data, mock_user):
        """test user_imae_url"""
        mock_user.return_value = MagicMock()
        self.modules[
            'rocketc.openedx_dependencies'].get_profile_image_urls_for_user.return_value = {"full": "http://url_test"}
        result = self.block._user_image_url()
        self.assertEqual(result, "http://url_test")

        self.modules[
            'rocketc.openedx_dependencies'].get_profile_image_urls_for_user.return_value = {"full": "url_test"}

        result = self.block._user_image_url()
        self.assertEqual(result, "http://127.0.0.1/url_test")


class TestApiRocketChat(unittest.TestCase):
    """ Unit tests for ApiRocketChat Xblock"""

    def setUp(self):
        """Set up general variables"""

        user = "test_user"
        password = "test_password"
        server_url = "http://test_server"
        data = {"authToken": "test_token", "userId": "test_id"}

        with patch('rocketc.api_rocket_chat.requests.post') as mock_post:
            mock_post.return_value.json.return_value = data
            self.api = ApiRocketChat(user, password, server_url)

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
    def test_add_user_to_group(self, mock_request):
        """Test for the add group method"""
        method = "post"
        success = {'success': True}

        user_id = "test_user_id"
        room_id = "test_room_id"

        mock_request.return_value = success
        url_path = "groups.invite"

        data = {"roomId": room_id, "userId": user_id}

        response = self.api.add_user_to_group(user_id, room_id)
        mock_request.assert_called_with(method, url_path, data)
        self.assertTrue(response['success'])

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
    def test_change_user_role(self, mock_request):
        """Test for chage role method"""
        method = "post"
        success = {'success': True}

        user_id = "test_user_id"
        role = "test_role"

        mock_request.return_value = success
        url_path = "users.update"

        data = {"userId": user_id, "data": {"roles": [role]}}

        self.api.change_user_role(user_id, role)
        mock_request.assert_called_with(method, url_path, data)

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
    def test_create_group(self, mock_request):
        """Test for the create group method"""
        method = "post"
        success = {'success': True}

        name = "test_name"
        username = "test_user_name"

        mock_request.return_value = success
        url_path = "groups.create"

        data = {'name': name, "members": [username]}

        response = self.api.create_group(name, username)
        self.assertEquals(response, success)
        mock_request.assert_called_with(method, url_path, data)

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
    def test_create_token(self, mock_request):
        """Test for the create token method"""
        method = "post"
        success = {'success': True}

        username = "test_user_name"

        mock_request.return_value = success
        url_path = "users.createToken"

        data = {'username': username}

        response = self.api.create_token(username)

        mock_request.assert_called_with(method, url_path, data)
        self.assertTrue(response['success'])

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
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

        response = self.api.create_user(name, email, username)

        mock_request.assert_called_with(method, url_path, data)
        self.assertTrue(response['success'])

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
    def test_get_groups(self, mock_request):
        """Test the method to get a group list"""
        method = "get"
        url_path = "groups.list"

        groups = {"groups": [{"name": "group1"}]}
        mock_request.return_value = groups

        return_value = self.api.get_groups()

        mock_request.assert_called_with(method, url_path)
        self.assertIn("group1", return_value)

        mock_request.return_value = {}

        return_value = self.api.get_groups()

        self.assertFalse(return_value)

    @patch('rocketc.api_rocket_chat.requests.post')
    def test_login(self, mock_request):
        """"""
        user = "test_user"
        password = "test_password"
        url = "/".join([self.api.server_url, self.api.API_PATH, "login"])
        data = {"user": user, "password": password}

        mock_request.return_value = MagicMock(status_code=200)
        mock_request.return_value.json.return_value = {
            "data": {"authToken": "test_token", "userId": "test_id"}}

        self.api._login(user, password)

        mock_request.assert_called_with(
            url=url, json=data, headers=self.api.headers)
        self.assertEqual(self.api.headers["X-Auth-Token"], "test_token")
        self.assertEqual(self.api.headers["X-User-Id"], "test_id")

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
    def test_convert_to_private_channel(self, mock_request):
        """Test for private channel method"""
        method = "post"
        room_name = "test_room_name"
        url_path = "channels.setType"
        data = {"roomId": "1234", "type": "p"}

        mock_request.return_value = {"channel": {"t": "c", "_id": "1234"}}
        self.api.convert_to_private_channel(room_name)

        mock_request.assert_called_with(method,  url_path, data)

    def test_request_rocket_chat(self):
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

        with patch('rocketc.api_rocket_chat.requests.post') as mock_post:
            mock_post.return_value.json.return_value = users
            data_post = self.api._request_rocket_chat("post", "users.create")

        with patch('rocketc.api_rocket_chat.requests.get') as mock_get:
            mock_get.return_value.json.return_value = info
            data_get = self.api._request_rocket_chat("get", "info")

        self.assertEqual(data_post, users)
        self.assertEqual(data_get, info)

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
    def test_search_rocket_chat_group(self, mock_request):
        """Test for the search group method"""
        method = "get"
        success = {'success': True}
        room_name = "test_room_name"
        mock_request.return_value = success
        url_path = "groups.info"
        payload = {"roomName": room_name}

        response = self.api.search_rocket_chat_group(room_name)

        mock_request.assert_called_with(method, url_path, payload=payload)
        self.assertTrue(response['success'])

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
    def test_search_rocket_chat_user(self, mock_request):
        """Test for the search user method"""
        method = "get"
        success = {'success': True}
        username = "test_user_name"
        mock_request.return_value = success
        url_path = "users.info"
        payload = {"username": username}

        response = self.api.search_rocket_chat_user(username)

        mock_request.assert_called_with(method, url_path, payload=payload)
        self.assertTrue(response['success'])

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
    def test_set_avatar(self, mock_request):
        """Test the method for set the avatar in RocketChat"""
        method = "post"
        username = "test_user_name"
        url = "test_url"

        url_path = "users.setAvatar"

        data = {"username": username, "avatarUrl": url}
        self.api.set_avatar(username, url)
        mock_request.assert_called_with(method, url_path, data)

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
    def test_set_group_description(self, mock_request):
        """
        This method tests the method set_description
        """
        description = None
        group_id = "test_id"

        return_none = self.api.set_group_description(group_id, description)

        self.assertIsNone(return_none)

        description = "test_description"

        url_path = "groups.setDescription"
        data = {"roomId": group_id, "description": description}
        method = "post"

        self.api.set_group_description(group_id, description)
        mock_request.assert_called_with(method, url_path, data)

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
    def test_set_group_topic(self, mock_request):
        """
        This method test the method set_topic
        """
        topic = None
        group_id = "test_id"

        return_none = self.api.set_group_topic(group_id, topic)

        self.assertIsNone(return_none)

        topic = "test_topic"

        url_path = "groups.setTopic"
        data = {"roomId": group_id, "topic": topic}
        method = "post"

        self.api.set_group_topic(group_id, topic)
        mock_request.assert_called_with(method, url_path, data)

    @patch('rocketc.api_rocket_chat.ApiRocketChat._request_rocket_chat')
    def test_update_user(self, mock_request):
        """Test the method to update the profile user"""
        method = "post"
        success = {'success': True}

        user_id = "test_user_id"
        email = "test_email"

        mock_request.return_value = success
        url_path = "users.update"

        data = {"userId": user_id, "data": {"email": email}}

        new_email = self.api.update_user(user_id, email)

        self.assertEqual(new_email, email)
        mock_request.assert_called_with(method, url_path, data)


class TestApiTeams(unittest.TestCase):
    """"""

    def setUp(self):
        """Set up general variables"""
        username = "test_user_name"
        password = "test_password"
        server_url = "http://test_server"
        client_secret = "test_client_secret"
        client_id = "test_client_id"

        with patch('rocketc.api_teams.ApiTeams._get_token') as mock_token:
            mock_token.return_value = "test_token"
            self.api = ApiTeams(username, password, client_id, client_secret, server_url)

    @patch('rocketc.api_teams.requests.get')
    def test_call_api_get(self, mock_request):
        """Test for the method call api get"""
        url_path = "test_path"
        payload = {"data": "data_test"}
        url = "/".join([self.api.server_url, self.api.API_PATH, url_path])

        self.api._call_api_get(url_path, payload)
        mock_request.assert_called_with(url, headers=self.api.headers, params=payload)

    # def test_get_user_team(self, course_id, username):
    #     """Get the user's team"""
    #     course_id = MagicMock()
    #     username = "test_user_name"
    #     url_path = "teams"
    #     payload = {"course_id": course_id, "username": username}
    #     team_request = self._call_api_get(url_path, payload)

    #     if team_request.status_code == 200:
    #         return team_request.json()["results"]
    #     return team_request.json()
