"""TO-DO: Write a description of what this XBlock is."""
import json
import hashlib
import pkg_resources
import requests

from xblock.core import XBlock
from xblock.fields import Integer, Scope, String
from xblock.fragment import Fragment


@XBlock.wants("user")
class RocketChatXBlock(XBlock):
    """
    TO-DO: document what your XBlock does.
    """

    # Fields are defined on the class.  You can access them in your code as
    # self.<fieldname>.

    # TO-DO: delete count, and define your own fields.
    count = Integer(
        default=0, scope=Scope.user_state,
        help="A simple counter, to show something happening",
    )

    url_prefix = "http://192.168.0.16:3000/api/v1"
    salt = "HarryPotter_y_elPrisonero_deAzkaban"

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    # TO-DO: change this view to display your data your own way.
    def student_view(self, context=None):
        """
        The primary view of the RocketChatXBlock, shown to students
        when viewing courses.        """
        self.get_admin_token_and_id()
        self.get_and_set_user()
        self.change = None
        response = self.login(self.username)
        if response['success']:
            self.response = response['data']
            self.auth_token = self.response['authToken']
            self.user_id = self.response['userId']
            self.add_to_course_group(self.course, self.user_id)
            if self.role == "instructor":
                self.change_role(self.user_id)
        else:
            self.response = response['errorType']
        html = self.resource_string("static/html/rocketc.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/rocketc.css"))
        frag.add_javascript(self.resource_string("static/js/src/rocketc.js"))
        frag.initialize_js('RocketChatXBlock')
        return frag

    # TO-DO: change this handler to perform your own actions.  You may need more
    # than one handler, or you may not need any handlers at all.
    @XBlock.json_handler
    def increment_count(self, data, suffix=''):
        """
        An example handler, which increments the data.
        """
        # Just to show data coming in...
        assert data['hello'] == 'world'

        self.count += 1
        return {"count": self.count}

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
#/////////////////////////////////////////////////////////////////////////

    def get_and_set_user(self):
        """
        This method initializes the user's parameters
        """
        runtime = self.xmodule_runtime
        self.role = runtime.get_user_role()
        self.anonymous_student_id = runtime.anonymous_student_id
        user = runtime.service(self, 'user').get_current_user()
        self.email = user.emails[0]
        self.username = user.opt_attrs['edx-platform.username']
        self.course = runtime.course_id.course

    def get_admin_token_and_id(self):
        """
        This method initializes admin's authToken and userId
        """
        url = "{}/{}".format(self.url_prefix, "login")
        data = {"user": "andrey92", "password": "edunext"}
        headers = {"Content-type": "application/json"}
        response = requests.post(url=url, json=data, headers=headers)
        self.admin_auth_token = response.json()["data"]["authToken"]
        self.admin_user_id = response.json()["data"]["userId"]

    def search_rocket_chat_user(self, username):
        """
        This method allows to get a user from RocketChat data base
        """
        url_path = "{}?{}={}".format("users.info", "username", username)

        return self.request_rocket_chat("get", url_path)

    def login(self, username):
        """
        This method allows to get the user's authToken and id 
        or creates a user to login in RocketChat
        """
        rocket_chat_user = self.search_rocket_chat_user(username)

        if rocket_chat_user['success']:
            data = self.create_token(username)

        else:
            self.create_user(self.anonymous_student_id,
                             self.email, self.username)
            data = self.create_token(username)

        return data

    def create_token(self, username):
        """
        This method generates a token that allows to login
        """
        url_path = "users.createToken"
        data = {'username': username}
        return self.request_rocket_chat("post", url_path, data)

    def change_role(self, user_id):
        """
        This method allows to change the user's role
        """
        data = {"userId": user_id, "data": {"roles": ["bot"]}}
        self.change = self.request_rocket_chat(
            "post", "users.update", data)['success']

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

        self.group = self.search_rocket_chat_group(group_name)

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

    def add_to_channel(self, room_name, username):
        """
        -----
        """
        room_id = self.get_room_id(room_name)
        user_id = self.get_user_id(username)
        data = {"roomId": room_id, "userId": user_id}
        self.request_rocket_chat("post", "channels.invite", data)

    def get_room_id(self, room_name):
        """
        -------
        """
        url_path = "{}?{}".format("channels.info", room_name)
        return self.request_rocket_chat("get", url_path)["channel"]["_id"]

    def request_rocket_chat(self, method, url_path, data=None):
        """
        This method generates a call to the RocketChat API and returns a json with the response
        """
        headers = {"X-Auth-Token": self.admin_auth_token,
                   "X-User-Id": self.admin_user_id, "Content-type": "application/json"}
        url = "{}/{}".format(self.url_prefix, url_path)
        if method == "post":
            response = requests.post(url=url, json=data, headers=headers)
        else:
            response = requests.get(url=url, headers=headers)
        return response.json()
