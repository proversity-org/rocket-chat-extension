"""TO-DO: Write a description of what this XBlock is."""

import pkg_resources
from xblock.core import XBlock
from xblock.fields import Integer, Scope, String
from xblock.fragment import Fragment
#///////////////////////////////////////////////////////////////
import requests
import json


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
        self.change_role()
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
        role = self.xmodule_runtime
        self.role = role.get_user_role()

    def get_admin_token_and_id(self):
        url = "{}/{}".format(self.url_prefix, "login")
        data = {"user": "andrey92", "password": "edunext"}
        headers = {"Content-type": "application/json"}
        r = requests.post(url=url, json=data, headers=headers)
        self.admin_authToken = r.json()["data"]["authToken"]
        self.admin_userId = r.json()["data"]["userId"]

    def change_role(self):

        data = {"userId": "test1234", "data": {"roles": "['bot']"}}
        self.change = self.request_rocket_chat("users.update", data)["success"]

    def create_user(self):

        data = {"name": "test1", "email": "email@user.tld",
                "password": "1234", "username": "uniqueusername"}
        return self.request_rocket_chat("users.create", data)["success"]

    def add_to_channel(self, roomName, userName):
        roomId = get_roomId(roomName)
        userId = get_userId(userName)
        data = {"roomId":roomId, "userId": userId}
        request_rocket_chat("channels.invite", data)


    def get_roomId(self, roomName):

        url_path = "{}?{}".format("channels.info", roomName)
        return self.request_rocket_chat(url_path)["channel"]["_id"]

    def request_rocket_chat(self, url_path, data=None):

        headers = {"X-Auth-Token": self.admin_authToken,
                   "X-User-Id": self.admin_userId, "Content-type": "application/json"}
        url = "{}/{}".format(self.url_prefix, url_path)
        r = requests.post(url=url, json=data, headers=headers)
        return r.json()
