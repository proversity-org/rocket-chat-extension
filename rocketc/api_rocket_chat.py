"""
This file contains the class with the necessary methos to use rocketchat
"""
import hashlib
import logging
import requests

LOG = logging.getLogger(__name__)


class ApiRocketChat(object):

    API_PATH = 'api/v1'
    salt = "HarryPotter_and_thePrisoner_of _Azkaban"

    def __init__(self, user, password, server_url="http://127.0.0.1:3000"):
        """Creates a RocketChat object and does login on the specified server"""
        self.server_url = server_url
        self.session = requests.Session()
        self._login(user, password)

    def _login(self, user, password):
        """This method defines the headers with the authToken and userId"""
        headers = {"Content-type": "application/json"}
        url = "/".join([self.server_url, self.API_PATH, "login"])
        data = {"user": user, "password": password}
        response = self.session.post(url=url, json=data, headers=headers)
        if response.status_code == 200:
            response = response.json()["data"]
            update_headers = {"X-Auth-Token": response["authToken"],
                              "X-User-Id": response["userId"],
                             }
            update_headers.update(headers)
            self.session.headers.update(update_headers)

            LOG.info("Auth_token: %s, User_id: %s ", update_headers[
                "X-Auth-Token"], update_headers["X-User-Id"])

    def _request_rocket_chat(self, method, url_path, data=None, payload=None):
        """
        This method generates a call to the RocketChat API and returns a json with the response
        """
        url = "/".join([self.server_url, self.API_PATH, url_path])
        if method == "post":
            response = self.session.post(url=url, json=data)
            LOG.info("Request rocketChat status code = %s",
                     response.status_code)
        else:
            response = self.session.get(url=url, params=payload)
            LOG.info("Request rocketChat status code = %s",
                     response.status_code)
        return response.json()

    def add_user_to_group(self, user_id, room_id):
        """
        This method add any user to any group
        """
        url_path = "groups.invite"
        data = {"roomId": room_id, "userId": user_id}
        response = self._request_rocket_chat("post", url_path, data)
        LOG.info("Method Add to Group: %s with this data: %s", response, data)
        return response

    def change_user_role(self, user_id, role):
        """
        This method allows to change the user's role
        """
        url_path = "users.update"
        data = {"userId": user_id, "data": {"roles": [role]}}
        response = self._request_rocket_chat(
            "post", url_path, data)
        if response["success"]:
            return role

    def create_group(self, name, usernames=[""], **kwargs):
        """
        This method creates a group with a specific name.
        """
        url_path = "groups.create"
        data = {"name": name, "members": usernames}
        data.update(kwargs)
        response = self._request_rocket_chat("post", url_path, data)
        LOG.info("Method Create Group: %s with this data: %s", response, data)
        return response

    def create_token(self, username):
        """
        This method generates a token that allows to login
        """
        url_path = "users.createToken"
        data = {'username': username}
        response = self._request_rocket_chat("post", url_path, data)
        LOG.info("Method Create Token: %s with this data: %s", response, data)
        return response

    def create_user(self, name, email, username):
        """
        This method creates a user with a specific name, username, email and password.
        The password is a result from a SHA1 function with the name and salt.
        """
        url_path = "users.create"
        password = "{}{}".format(name, self.salt)
        password = hashlib.sha1(password).hexdigest()
        data = {"name": name, "email": email,
                "password": password, "username": username}
        response = self._request_rocket_chat("post", url_path, data)
        LOG.info("Method Create User: %s with this data: %s", response, data)
        return response

    def get_groups(self, **kwargs):
        """
        This method lists the existing groups
        """
        url_path = "groups.list"
        method = "get"
        payload = kwargs
        response = self._request_rocket_chat(method, url_path, payload=payload)
        list_groups = []

        if "groups" in response:
            for group in response["groups"]:
                list_groups.append(group["name"])

        return list_groups

    def convert_to_private_channel(self, room_name):
        """
        This method changes channels from public to private
        the channel's type is define as t, when t = c is a public channel
        and when t = p is a private channel
        """
        url_path = "channels.info"
        payload = {"roomName": room_name}
        channel = self._request_rocket_chat("get", url_path, payload=payload)

        if "channel" in channel and channel["channel"]["t"] == "c":
            channel_id = channel["channel"]["_id"]
            url_path = "channels.setType"
            data = {"roomId": channel_id, "type": "p"}
            self._request_rocket_chat("post", url_path, data)

    def search_rocket_chat_group(self, room_name):
        """
        This method gets a group with a specific name and returns a json with group's info
        """
        url_path = "groups.info"
        payload = {"roomName": room_name}
        return self._request_rocket_chat("get", url_path, payload=payload)

    def search_rocket_chat_user(self, username):
        """
        This method allows to get a user from RocketChat data base
        """
        url_path = "users.info"
        payload = {"username": username}

        return self._request_rocket_chat("get", url_path, payload=payload)

    def set_avatar(self, username, image_url):
        """
        This method allows to set the profile photo/avatar
        """
        url_path = "users.setAvatar"
        data = {"username": username, "avatarUrl": image_url}
        response = self._request_rocket_chat("post", url_path, data)
        LOG.info("Method set avatar: %s with this data: %s", response, data)

    def set_group_description(self, group_id, description):
        """
        This method allows to set a description's group
        """
        if description == "" or description is None:
            return

        url_path = "groups.setDescription"
        data = {"roomId": group_id, "description": description}
        method = "post"

        response = self._request_rocket_chat(method, url_path, data)

        LOG.info("Method Set Description %s with this data: %s", response, data)

    def set_group_topic(self, group_id, topic):
        """
        This method allows to set a topic's group
        """
        if topic == "" or topic is None:
            return

        url_path = "groups.setTopic"
        data = {"roomId": group_id, "topic": topic}
        method = "post"

        response = self._request_rocket_chat(method, url_path, data)

        LOG.info("Method Set Topic: %s with this data: %s", response, data)

    def update_user(self, user_id, email):
        """
        This method allows to update The user data
        """
        url_path = "users.update"
        data = {"userId": user_id, "data": {"email": email}}
        response = self._request_rocket_chat("post", url_path, data)
        LOG.info("Method Update User: %s with this data: %s", response, data)
        if response["success"]:
            return email

    def kick_user_from_group(self, user_id, room_id):
        """
        Removes a user from the private group.
        """
        url_path = "groups.kick"
        data = {"roomId": room_id, "userId": user_id}
        response = self._request_rocket_chat("post", url_path, data)
        LOG.info(
            "Method Kick user from a Group: %s with this data: %s", response, data)
        return response

    def list_all_groups(self, user_id, auth_token, **kwargs):
        """Get a list of groups"""
        url_path = "groups.list"
        payload = kwargs
        url = "/".join([self.server_url, self.API_PATH, url_path])

        headers = {"X-User-Id": user_id, "X-Auth-Token": auth_token}

        response = requests.get(url=url, headers=headers, params=payload)
        LOG.info("Method list all groups: %s with this data: %s",
                 response, payload)
        return response.json()

    def get_groups_history(self, room_id, latest="", oldest="",  # pylint: disable=too-many-arguments
                           count=100, inclusive=False, unreads=False):
        """
        Retrieves the messages from a private group.
        """
        url_path = "groups.history"
        payload = {"roomId": room_id,
                   "latest": latest,
                   "oldest": oldest,
                   "count": count,
                   "inclusive": inclusive,
                   "unreads": unreads,
                  }
        return self._request_rocket_chat("get", url_path, payload=payload)

    def set_custom_fields(self, room_id, custom_fields):
        """
        Sets the custom fields for the private group.
        This receives the room id and a dict with the custom fields
        """
        url_path = "groups.setCustomFields"
        data = {"roomId": room_id, "customFields": custom_fields}
        method = "post"
        response = self._request_rocket_chat(method, url_path, data)
        LOG.info("Method set_custom_fields: %s with this data: %s", response, data)
        return response

    def logout_user(self, user_id, login_token):
        """
        This method allows to logout an user
        """
        url_path = "logout"
        headers = {"X-Auth-Token": login_token, "X-User-Id": user_id}
        url = "{}/{}/{}".format(self.server_url, self.API_PATH, url_path)
        response = requests.get(url=url, headers=headers)
        LOG.info("Method logout User: %s ", response)
        return response
