"""TO-DO: Write a description of what this XBlock is."""

import pkg_resources
from xblock.core import XBlock
from xblock.fields import Integer, Scope, String
from xblock.fragment import Fragment
#///////////////////////////////////////////////////////////////
import requests
import json


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

    url_prefix = "http://192.168.0.22:3000/api/v1"

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
            self.authToken = self.response['authToken']
            self.userid = self.response['userId']
            self.add_to_course_group(self.course, self.userid)
            if self.role == "instructor":
                self.change_role(self.userid)
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
        """
        url = "{}/{}".format(self.url_prefix, "login")
        data = {"user": "andrey92", "password": "edunext"}
        headers = {"Content-type": "application/json"}
        r = requests.post(url=url, json=data, headers=headers)
        self.admin_authToken = r.json()["data"]["authToken"]
        self.admin_userId = r.json()["data"]["userId"]

    def search_rocket_chat_user(self, username):
        """
        """
        url_path = "{}?{}={}".format("users.info", "username", username)

        return self.request_rocket_chat("get", url_path)

    def login(self, username):
        """
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
        """
        url_path = "users.createToken"
        data = {'username': username}
        return self.request_rocket_chat("post", url_path, data)

    def change_role(self, userid):

        data = {"userId": userid, "data": {"roles": ["bot"]}}
        self.change = self.request_rocket_chat(
            "post", "users.update", data)['success']

    def create_user(self, name, email, username):
        """
        """
        data = {"name": name, "email": email,
                "password": "edx", "username": username}
        return self.request_rocket_chat("post", "users.create", data)

    def add_to_course_group(self, groupname, userid):

        rocket_chat_group = self.search_rocket_chat_group(groupname)

        if rocket_chat_group['success']:
            self.add_to_group(userid, rocket_chat_group['group']['_id'])
        else:
            rocket_chat_group = self.create_group(groupname)
            self.add_to_group(userid, rocket_chat_group['group']['_id'])

        self.group = self.search_rocket_chat_group(groupname)

    def search_rocket_chat_group(self, name):

        url_path = "{}?{}={}".format("groups.info", "roomName", name)
        return self.request_rocket_chat("get", url_path)

    def add_to_group(self, userid, roomid):

        url_path = "groups.invite"
        data = {"roomId": roomid, "userId": userid}
        return self.request_rocket_chat("post", url_path, data)

    def create_group(self, name):
        url_path = "groups.create"
        data = {"name": name}
        self.request_rocket_chat("post", url_path, data)

    def add_to_channel(self, roomname, username):
        roomId = get_roomId(roomname)
        userId = get_userId(username)
        data = {"roomId": roomId, "userId": userId}
        self.request_rocket_chat("post", "channels.invite", data)

    def get_roomId(self, roomname):

        url_path = "{}?{}".format("channels.info", roomname)
        return self.request_rocket_chat("get", url_path)["channel"]["_id"]

    def request_rocket_chat(self, method, url_path, data=None):

        headers = {"X-Auth-Token": self.admin_authToken,
                   "X-User-Id": self.admin_userId, "Content-type": "application/json"}
        url = "{}/{}".format(self.url_prefix, url_path)
        if method == "post":
            r = requests.post(url=url, json=data, headers=headers)
        else:
            r = requests.get(url=url, headers=headers)
        return r.json()
