"""
TO-DO: Write a description of what this XBlock is.
"""
import hashlib
import re
import pkg_resources
import requests

from django.conf import settings
from django.contrib.auth.models import User

from xblock.core import XBlock
from xblock.fields import Scope, String, Boolean
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from xblockutils.settings import XBlockWithSettingsMixin
from xblockutils.studio_editable import StudioEditableXBlockMixin


LOADER = ResourceLoader(__name__)
LOG = logging.getLogger(__name__)


@XBlock.wants("user")  # pylint: disable=too-many-ancestors
@XBlock.wants("settings")
class RocketChatXBlock(XBlock, XBlockWithSettingsMixin, StudioEditableXBlockMixin):
    """
    This class allows to embed a chat window inside a unit course
    and set the necessary variables to config the rocketChat enviroment
    """
    display_name = String(
        display_name="Display Name",
        scope=Scope.settings,
        default="Rocket Chat"
    )
    email = String(
        default="", scope=Scope.user_state,
        help="Email in rocketChat",
    )
    rocket_chat_role = String(
        default="user", scope=Scope.user_state,
        help="The defined role in rocketChat"
    )

    default_channel = String(
        display_name="Default Channel",
        default="",
        scope=Scope.content,
        help="This field allows to select the channel that would be accesible in the unit",
        values_provider=lambda self: self.get_groups(),
    )
    default_group_enable = Boolean(
        default=False,
        scope=Scope.user_state,
        help="This is the flag for the initial channel",
    )

    salt = "HarryPotter_and_thePrisoner_of _Azkaban"

    # Possible editable fields
    editable_fields = ('default_channel', )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        # pylint: disable=no-self-use
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def student_view(self, context=None):
        """
        The primary view of the RocketChatXBlock, shown to students
        when viewing courses.
        """

        in_studio_runtime = hasattr(
            self.xmodule_runtime, 'is_author_mode')  # pylint: disable=no-member

        if in_studio_runtime:
            return self.author_view(context)

        context["response"] = self.init()
        context["user_data"] = self.user_data
        context["default_group_enable"] = self.default_group_enable
        context["public_url_service"] = self.server_data["public_url_service"]

        frag = Fragment(LOADER.render_template(
            'static/html/rocketc.html', context))
        frag.add_css(self.resource_string("static/css/rocketc.css"))
        frag.add_javascript(self.resource_string("static/js/src/rocketc.js"))
        frag.initialize_js('RocketChatXBlock')
        return frag

    def author_view(self, context=None):
        """  Returns author view fragment on Studio """
        # pylint: disable=unused-argument
        self._private_channel("general")
        frag = Fragment(u"Studio Runtime RocketChatXBlock")
        frag.add_css(self.resource_string("static/css/rocketc.css"))
        frag.add_javascript(self.resource_string("static/js/src/rocketc.js"))
        frag.initialize_js('RocketChatXBlock')

        return frag

    def studio_view(self, context=None):
        """  Returns edit studio view fragment """
        frag = super(RocketChatXBlock, self).studio_view(context)
        frag.add_content(LOADER.render_template(
            'static/html/studio.html', context))
        frag.add_css(self.resource_string("static/css/rocketc.css"))
        frag.add_javascript(self.resource_string("static/js/src/studio_view.js"))
        frag.initialize_js('StudioViewEdit')
        return frag

    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("RocketChatXBlock",
             """<rocketc/>
             """),
            ("Multiple RocketChatXBlock",
             """<vertical_demo>
                <rocketc/>
                <rocketc/>
                <rocketc/>
                </vertical_demo>
             """),
        ]

    @property
    def admin_data(self):
        """
        This property allows to use in the internal methods self.admin_data
        as a class' field
        """
        try:
            user = self.xblock_settings["admin_user"]
            password = self.xblock_settings["admin_pass"]
        except KeyError:
            LOG.exception("The admin's settings has not been found")
            raise

        url = "{}/{}".format(self.url_api_rocket_chat, "login")
        data = {"user": user, "password": password}
        headers = {"Content-type": "application/json"}
        response = requests.post(url=url, json=data, headers=headers)
        admin_data = {}
        admin_data["auth_token"] = response.json()["data"]["authToken"]
        admin_data["user_id"] = response.json()["data"]["userId"]

        LOG.info("Auth_token: %s, User_id: %s ", admin_data[
            "auth_token"], admin_data["user_id"])

        return admin_data

    @property
    def url_api_rocket_chat(self):
        """
        This method retunrs the rocketChat url service where someone can acces to API
        """
        server_data = self.server_data
        if "private_url_service" in server_data:
            return "/".join([server_data["private_url_service"], "api", "v1"])
        LOG.warning("The request will be made to localhost")
        return "/".join(["http://localhost:3000", "api", "v1"])

    @property
    def user_data(self):
        """
        This method initializes the user's parameters
        """
        runtime = self.xmodule_runtime  # pylint: disable=no-member
        user = runtime.service(self, 'user').get_current_user()
        user_data = {}
        user_data["email"] = user.emails[0]
        user_data["role"] = runtime.get_user_role()
        user_data["course_id"] = runtime.course_id
        user_data["course"] = re.sub('[^A-Za-z0-9]+', '', runtime.course_id._to_string()) # pylint: disable=protected-access
        user_data["username"] = user.opt_attrs['edx-platform.username']
        user_data["anonymous_student_id"] = runtime.anonymous_student_id
        user_data["default_group"] = self.default_channel
        return user_data

    @property
    def server_data(self):
        """
        This method allows to get private and public url from xblock settings
        """
        xblock_settings = self.xblock_settings
        server_data = {}
        server_data["private_url_service"] = xblock_settings["private_url_service"]
        server_data["public_url_service"] = xblock_settings["public_url_service"]
        return server_data

    @property
    def xblock_settings(self):
        """
        This method allows to get the xblock settings
        """
        return self.get_xblock_settings()

    def init(self):
        """
        This method initializes the user's variables and
        log in to rocketchat account
        """

        user_data = self.user_data

        response = self.login(user_data)
        if response['success']:
            response = response['data']
            user_id = response['userId']
            self._add_to_team_group(user_id, user_data["username"], user_data["course_id"])
            self._update_user(user_id, user_data["username"], user_data["email"])
            self.add_to_course_group(
                user_data["course"], user_id)
            self.default_group_enable = self._add_to_default_group(
                self.default_channel, user_id)
            if user_data["role"] == "instructor" and self.rocket_chat_role == "user":
                self.change_role(user_id, "bot")
            return response
        else:
            return response['errorType']

    def search_rocket_chat_user(self, username):
        """
        This method allows to get a user from RocketChat data base
        """
        url_path = "{}?{}={}".format("users.info", "username", username)

        return self._request_rocket_chat("get", url_path)

    def login(self, user_data):
        """
        This method allows to get the user's authToken and id
        or creates a user to login in RocketChat
        """
        rocket_chat_user = self.search_rocket_chat_user(user_data["username"])
        LOG.info("Login method: result search user: %s", rocket_chat_user["success"])

        if rocket_chat_user['success']:
            data = self.create_token(user_data["username"])

        else:
            response = self.create_user(user_data["anonymous_student_id"], user_data[
                "email"], user_data["username"])
            LOG.info("Login method: result create user : %s", response)
            data = self.create_token(user_data["username"])

        LOG.info("Login method: result create token: %s", data)

        return data

    def create_token(self, username):
        """
        This method generates a token that allows to login
        """
        url_path = "users.createToken"
        data = {'username': username}
        return self._request_rocket_chat("post", url_path, data)

    def change_role(self, user_id, role):
        """
        This method allows to change the user's role
        """
        data = {"userId": user_id, "data": {"roles": [role]}}
        response = self._request_rocket_chat(
            "post", "users.update", data)
        if response["success"]:
            self.rocket_chat_role = role

    def create_user(self, name, email, username):
        """
        This method creates a user with a specific name, username, email and password.
        The password is a result from a SHA1 function with the name and salt.
        """
        password = "{}{}".format(name, self.salt)
        password = hashlib.sha1(password).hexdigest()
        data = {"name": name, "email": email,
                "password": password, "username": username}
        return self._request_rocket_chat("post", "users.create", data)

    def add_to_course_group(self, group_name, user_id):
        """
        This method add the user to the default course channel
        """
        rocket_chat_group = self._search_rocket_chat_group(group_name)

        if rocket_chat_group['success']:
            self._add_to_group(user_id, rocket_chat_group['group']['_id'])
        else:
            rocket_chat_group = self._create_group(group_name, self.user_data["username"])

        self.group = self._search_rocket_chat_group(  # pylint: disable=attribute-defined-outside-init
            group_name)

    def _search_rocket_chat_group(self, room_name):
        """
        This method gets a group with a specific name and returns a json with group's info
        """
        url_path = "{}?{}={}".format("groups.info", "roomName", room_name)
        return self._request_rocket_chat("get", url_path)

    def _add_to_group(self, user_id, room_id):
        """
        This method add any user to any group
        """
        url_path = "groups.invite"
        data = {"roomId": room_id, "userId": user_id}
        response = self._request_rocket_chat("post", url_path, data)
        LOG.info("Method Add to Group: %s with this data: %s", response, data)
        return response

    def _create_group(self, name, username=""):
        """
        This method creates a group with a specific name.
        """
        url_path = "groups.create"
        data = {"name": name, "members": [username]}
        response = self._request_rocket_chat("post", url_path, data)
        LOG.info("Method Create Group: %s with this data: %s", response, data)
        return response

    def _request_rocket_chat(self, method, url_path, data=None):
        """
        This method generates a call to the RocketChat API and returns a json with the response
        """
        headers = {"X-Auth-Token": self.admin_data["auth_token"],
                   "X-User-Id": self.admin_data["user_id"], "Content-type": "application/json"}
        url = "{}/{}".format(self.url_api_rocket_chat, url_path)
        if method == "post":
            response = requests.post(url=url, json=data, headers=headers)
        else:
            response = requests.get(url=url, headers=headers)
        return response.json()

    def _user_image_url(self):
        """Returns an image url for the current user"""
        from openedx_dependencies import get_profile_image_urls_for_user  # pylint: disable=relative-import
        current_user = User.objects.get(username=self.user_data["username"])
        profile_image_url = get_profile_image_urls_for_user(current_user)[
            "full"]

        if profile_image_url.startswith("http"):
            return profile_image_url

        base_url = settings.LMS_ROOT_URL
        image_url = "{}{}".format(base_url, profile_image_url)
        LOG.info("User image url: %s ", image_url)
        return image_url

    def _set_avatar(self, username):
        image_url = self._user_image_url()
        url_path = "users.setAvatar"
        data = {"username": username, "avatarUrl": image_url}
        response = self._request_rocket_chat("post", url_path, data)
        LOG.info("Method set avatar: %s with this data: %s", response, data)

    def _update_user(self, user_id, username, email):
        """
        This method allows to update The user data
        """
        if email != self.email:
            url_path = "users.update"
            data = {"userId": user_id, "data": {"email": email}}
            response = self._request_rocket_chat("post", url_path, data)
            LOG.info("Method Update User: %s with this data: %s", response, data)
            if response["success"]:
                self.email = email
        self._set_avatar(username)

    @XBlock.json_handler
    def create_group(self, data, suffix=""):
        """
        This method allows to create a group from studio
        """
        # pylint: disable=unused-argument

        group_name = data["groupName"]
        description = data["description"]
        topic = data["topic"]

        if group_name == "" or group_name is None:
            return {"success": False, "error": "Group Name is not valid"}

        group_name = group_name.replace(" ", "_")
        group = self._create_group(group_name)

        if group["success"]:
            self.default_channel = group_name

        if "group" in group:
            group_id = group["group"]["_id"]

            self._set_description(group_id, description)
            self._set_topic(group_id, topic)

        LOG.info("Method Public Create Group: %s", group)
        return group

    def _add_to_default_group(self, group_name, user_id):
        """
        """
        group_info = self._search_rocket_chat_group(group_name)

        if group_info["success"]:
            self._add_to_group(user_id, group_info['group']['_id'])
            return True
        return False

    def get_groups(self):
        """
        This method lists the existing groups
        """
        url_path = "groups.list"
        method = "get"
        response = self._request_rocket_chat(method, url_path)
        list_groups = []

        if "groups" in response:
            for group in response["groups"]:
                list_groups.append(group["name"])

        return list_groups

    def _private_channel(self, room_name):
        """
        This method changes channels from public to private
        the channel's type is define as t, when t = c is a public channel
        and when t = p is a private channel
        """
        url_search = "{}?{}={}".format("channels.info", "roomName", room_name)
        channel = self._request_rocket_chat("get", url_search)

        if "channel" in channel and channel["channel"]["t"] == "c":
            channel_id = channel["channel"]["_id"]
            url_path = "channels.setType"
            data = {"roomId": channel_id, "type": "p"}
            self._request_rocket_chat("post", url_path, data)

    def _set_description(self, group_id, description):
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

    def _set_topic(self, group_id, topic):
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

    @staticmethod
    def teams_is_enabled(course_id):
        """
        This method verifies if teams are available
        """
        from openedx_dependencies import modulestore  # pylint: disable=relative-import
        course = modulestore().get_course(course_id, depth=0)
        teams_configuration = course.teams_configuration
        if "topics" in teams_configuration and teams_configuration["topics"]:
            return True
        return False

    @staticmethod
    def _get_team(username, course_id):
        """
        This method gets the user's team
        """
        from openedx_dependencies import CourseTeam  # pylint: disable=relative-import
        result_filter = {"course_id": course_id, 'membership__user__username': username}
        team = CourseTeam.objects.filter(**result_filter)
        if team:
            return team[0]
        return None

    def _add_to_team_group(self, user_id, username, course_id):
        """

        """
        team = self._get_team(username, course_id)

        if team is None:
            return False

        group_name = "-".join(["Team", team.topic_id, team.name])
        group_info = self._search_rocket_chat_group(group_name)

        if group_info["success"]:
            response = self._add_to_group(user_id, group_info['group']['_id'])
            return response["success"]

        response = self._create_group(group_name, username)
        return response["success"]
