"""
TO-DO: Write a description of what this XBlock is.
"""
import hashlib
import pkg_resources
import requests

from django.conf import settings
from django.contrib.auth.models import User
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_urls_for_user

from xblock.core import XBlock
from xblock.fields import Integer, Scope, String
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader

LOADER = ResourceLoader(__name__)
URL_PREFIX = "http://192.168.0.16:3000/api/v1"

@XBlock.wants("user") # pylint: disable=too-many-ancestors
class RocketChatXBlock(XBlock):
    """
    This class allows to embed a chat window inside a unit course
    and set the necessary variables to config the rocketChat enviroment
    """
    count = Integer(
        default=0, scope=Scope.user_state,
        help="A simple counter, to show something happening",
    )
    rocket_chat_role = String(
        default="user", scope=Scope.user_state,
        help="The defined role in rocketChat"
    )

    salt = "HarryPotter_and_thePrisoner_of _Azkaban"

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
        context["admin_data"] = self.admin_data

        url = self._user_image_url()

        frag = Fragment(LOADER.render_template(
            'static/html/rocketc.html', context))
        frag.add_css(self.resource_string("static/css/rocketc.css"))
        frag.add_javascript(self.resource_string("static/js/src/rocketc.js"))
        frag.initialize_js('RocketChatXBlock')
        return frag

    def author_view(self, context=None):
        """  Returns author view fragment on Studio """
        # pylint: disable=unused-argument
        frag = Fragment(u"Studio Runtime RocketChatXBlock")
        frag.add_css(self.resource_string("static/css/rocketc.css"))
        frag.add_javascript(self.resource_string("static/js/src/rocketc.js"))
        frag.initialize_js('RocketChatXBlock')

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

    def init(self):
        """
        This method initializes the user's variables and
        log in to rocketchat account
        """
        self.get_admin_data()
        self.get_user_data()

        response = self.login(self.user_data)
        if response['success']:
            response = response['data']
            self.add_to_course_group(
                self.user_data["course"], response['userId'])
            if self.user_data["role"] == "instructor" and self.rocket_chat_role == "user":
                self.change_role(response['userId'], "bot")
            return response
        else:
            return response['errorType']

    def get_user_data(self):
        """
        This method initializes the user's parameters
        """
        runtime = self.xmodule_runtime # pylint: disable=no-member
        user = runtime.service(self, 'user').get_current_user()
        user_data = {}
        user_data["email"] = user.emails[0]
        user_data["role"] = runtime.get_user_role()
        user_data["course"] = runtime.course_id.course
        user_data["username"] = user.opt_attrs['edx-platform.username']
        user_data["anonymous_student_id"] = runtime.anonymous_student_id
        self.user_data = user_data # pylint: disable=attribute-defined-outside-init

    def get_admin_data(self):
        """
        This method initializes admin's authToken and userId
        """
        url = "{}/{}".format(URL_PREFIX, "login")
        data = {"user": "andrey92", "password": "edunext"}
        headers = {"Content-type": "application/json"}
        response = requests.post(url=url, json=data, headers=headers)
        self.admin_data = {} # pylint: disable=attribute-defined-outside-init
        self.admin_data["auth_token"] = response.json()["data"]["authToken"]
        self.admin_data["user_id"] = response.json()["data"]["userId"]

    def search_rocket_chat_user(self, username):
        """
        This method allows to get a user from RocketChat data base
        """
        url_path = "{}?{}={}".format("users.info", "username", username)

        return self.request_rocket_chat("get", url_path)

    def login(self, user_data):
        """
        This method allows to get the user's authToken and id
        or creates a user to login in RocketChat
        """
        rocket_chat_user = self.search_rocket_chat_user(user_data["username"])

        if rocket_chat_user['success']:
            data = self.create_token(user_data["username"])

        else:
            self.create_user(user_data["anonymous_student_id"],
                             user_data["email"], user_data["username"])
            data = self.create_token(user_data["username"])

        return data

    def create_token(self, username):
        """
        This method generates a token that allows to login
        """
        url_path = "users.createToken"
        data = {'username': username}
        return self.request_rocket_chat("post", url_path, data)

    def change_role(self, user_id, role):
        """
        This method allows to change the user's role
        """
        data = {"userId": user_id, "data": {"roles": [role]}}
        response = self.request_rocket_chat(
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
        return self.request_rocket_chat("post", "users.create", data)

    def add_to_course_group(self, group_name, user_id):
        """
        This method add the user to the default course channel
        """
        rocket_chat_group = self.search_rocket_chat_group(group_name)

        if rocket_chat_group['success']:
            self.add_to_group(user_id, rocket_chat_group['group']['_id'])
        else:
            rocket_chat_group = self.create_group(group_name)
            self.add_to_group(user_id, rocket_chat_group['group']['_id'])

        self.group = self.search_rocket_chat_group(group_name) # pylint: disable=attribute-defined-outside-init

    def search_rocket_chat_group(self, room_name):
        """
        This method gets a group with a specific name and returns a json with group's info
        """
        url_path = "{}?{}={}".format("groups.info", "roomName", room_name)
        return self.request_rocket_chat("get", url_path)

    def add_to_group(self, user_id, room_id):
        """
        This method add any user to any group
        """
        url_path = "groups.invite"
        data = {"roomId": room_id, "userId": user_id}
        return self.request_rocket_chat("post", url_path, data)

    def create_group(self, name):
        """
        This method creates a group with a specific name.
        """
        url_path = "groups.create"
        data = {"name": name}
        self.request_rocket_chat("post", url_path, data)

    def request_rocket_chat(self, method, url_path, data=None):
        """
        This method generates a call to the RocketChat API and returns a json with the response
        """
        headers = {"X-Auth-Token": self.admin_data["auth_token"],
                   "X-User-Id": self.admin_data["user_id"], "Content-type": "application/json"}
        url = "{}/{}".format(URL_PREFIX, url_path)
        if method == "post":
            response = requests.post(url=url, json=data, headers=headers)
        else:
            response = requests.get(url=url, headers=headers)
        return response.json()

    def _user_image_url(self):
        """Returns an image urlfor the current user"""
        current_user = User.objects.get(username=self.user_data["username"])
        base_url = settings.LMS_ROOT_URL
        profile_image_url = get_profile_image_urls_for_user(current_user)["full"]
        image_url = "{}{}".format(base_url, profile_image_url)
        return image_url
