"""
This file contains the class with the necessary methods to use rocketchat
"""
import hashlib
import json
import logging
import requests
from rocketchat_API.rocketchat import RocketChat

LOG = logging.getLogger(__name__)


def handle_response(method, response, **kwargs):

    if response.status_code == 200:
        response = response.json()
        LOG.info("Method %s returns successfully from this data: %s", method, kwargs)
        return response
    LOG.info(
        "Method %s generates response with status code %s from this data: %s", method, response.status_code, kwargs
    )
    return json.loads(response.text)


class ApiRocketChat(RocketChat):

    salt = "HarryPotter_and_thePrisoner_of _Azkaban"

    def add_user_to_group(self, user_id, room_id):
        """
        This method add any user to any group
        """
        response = self.groups_invite(room_id, user_id)
        return handle_response("add_user_to_group", response, user_id=user_id, room_id=room_id)

    def change_user_role(self, user_id, role):
        """
        This method allows to change the user's role
        """
        response = self.users_update(user_id, data={"roles": [role]})
        if handle_response("change_user_role", response, user_id=user_id, role=role).get("success"):
            return role

    def create_group(self, name, usernames=[""], **kwargs):
        """
        This method creates a group with a specific name.
        """
        response = self.groups_create(name, members=usernames, **kwargs)
        return handle_response("create_group", response, name=name, members=usernames, **kwargs)

    def create_token(self, username):
        """
        This method generates a token that allows to login
        """
        response = self.users_create_token(username=username)
        return handle_response("create_token", response, username=username)

    def create_user(self, name, email, username):
        """
        This method creates a user with a specific name, username, email and password.
        The password is a result from a SHA1 function with the name and salt.
        """
        password = "{}{}".format(name, self.salt)
        password = hashlib.sha1(password).hexdigest()
        response = self.users_create(email, name, password, username)
        return handle_response("create_user", response, name=name, username=username, email=email)

    def get_groups(self, **kwargs):
        """
        This method lists the existing groups
        """
        response = self.groups_list_all(**kwargs)
        response = handle_response("get_groups", response, **kwargs)
        return [group["name"] for group in response.get("groups", [])]

    def convert_to_private_channel(self, room_name):
        """
        This method changes channels from public to private
        the channel's type is define as t, when t = c is a public channel
        and when t = p is a private channel
        """
        response = self.channels_info(channel=room_name)
        channel = handle_response("convert_to_private_channel", response, room_name=room_name)

        if "channel" in channel and channel["channel"]["t"] == "c":
            channel_id = channel["channel"]["_id"]
            self.channels_set_type(channel_id, "p")

    def search_rocket_chat_group(self, room_name):
        """
        This method gets a group with a specific name and returns a json with group's info
        """
        response = self.groups_info(room_name=room_name)
        return handle_response("search_rocket_chat_group", response, room_name=room_name)

    def search_rocket_chat_user(self, username):
        """
        This method allows to get a user from RocketChat data base
        """
        response = self.users_info(username=username)
        return handle_response("search_rocket_chat_user", response, username=username)

    def set_avatar(self, username, image_url):
        """
        This method allows to set the profile photo/avatar
        """
        response = self.users_set_avatar(image_url, username=username, avatarUrl=image_url)
        handle_response("set_avatar", response, username=username, image_url=image_url)

    def set_group_description(self, group_id, description):
        """
        This method allows to set a description's group
        """
        if description == "" or description is None:
            return

        response = self.groups_set_description(group_id, description)
        handle_response("set_group_description", response, group_id=group_id, description=description)

    def set_group_topic(self, group_id, topic):
        """
        This method allows to set a topic's group
        """
        if topic == "" or topic is None:
            return

        response = self.groups_set_topic(group_id, topic)
        handle_response("set_group_topic", response, group_id=group_id, topic=topic)

    def update_user(self, user_id, email):
        """
        This method allows to update The user data
        """
        response = self.users_update(user_id, data={"email": email})
        response = handle_response("update_user", response, user_id=user_id, email=email)
        if response["success"]:
            return email

    def kick_user_from_group(self, user_id, room_id):
        """
        Removes a user from the private group.
        """
        response = self.groups_kick(room_id, user_id)
        return handle_response("kick_user_from_group", response, user_id=user_id, room_id=room_id)

    def list_all_groups(self, user_id, auth_token, **kwargs):
        """Get a list of groups"""
        url_path = "groups.list"
        url = "{}{}{}".format(self.server_url, self.API_path, url_path)

        headers = {"X-User-Id": user_id, "X-Auth-Token": auth_token}

        return handle_response("list_all_groups", requests.get(url=url, headers=headers), **kwargs)

    def get_groups_history(self, room_id, latest="", oldest="",  # pylint: disable=too-many-arguments
                           count=100, inclusive=False, unreads=False):
        """
        Retrieves the messages from a private group.
        """
        kwargs = {
            "latest": latest,
            "oldest": oldest,
            "count": count,
            "inclusive": inclusive,
            "unreads": unreads,
        }
        response = self.groups_history(room_id, kwargs=kwargs)
        return handle_response("get_groups_history", response, room_id=room_id, kwargs=kwargs)

    def set_custom_fields(self, room_id, custom_fields):
        """
        Sets the custom fields for the private group.
        This receives the room id and a dict with the custom fields
        """
        response = self.__call_api_post("groups.setCustomFields", roomId=room_id, customFields=custom_fields)
        return handle_response("set_custom_fields", response)

    def logout_user(self, user_id, login_token):
        """
        This method allows to logout an user
        """
        url_path = "logout"
        headers = {"X-Auth-Token": login_token, "X-User-Id": user_id}
        url = "{}{}{}".format(self.server_url, self.API_path, url_path)
        response = requests.get(url=url, headers=headers)
        return handle_response("logout_user", response, user_id=user_id)
