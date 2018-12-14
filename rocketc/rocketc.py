"""
TO-DO: Write a description of what this XBlock is.
"""
import logging
import json
import re
import hashlib
import pkg_resources

from api_teams import ApiTeams  # pylint: disable=relative-import
from api_rocket_chat import ApiRocketChat  # pylint: disable=relative-import

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.cache import cache
from webob.response import Response

from xblock.core import XBlock
from xblock.fields import Scope, String, Boolean, DateTime, Integer, Float
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from xblockutils.settings import XBlockWithSettingsMixin
from xblockutils.studio_editable import StudioEditableXBlockMixin


LOADER = ResourceLoader(__name__)
LOG = logging.getLogger(__name__)
ROCKET_CHAT_DATA = "rocket_chat_data"
CACHE_TIMEOUT = 86400


def generate_custom_fields(course, team=None, specific_team=False):

    team_name, topic = generate_team_variables(team)
    return {
        "customFields": {
            "course": course,
            "team": team_name,
            "topic": topic,
            "specificTeam": specific_team,
        }
    }


def generate_query_dict(course, team=None, specific_team=False):

    team_name, topic = generate_team_variables(team)
    query = {
        "customFields.course": course,
        "customFields.team": team_name,
        "customFields.topic": topic,
        "customFields.specificTeam": specific_team,
    }
    return {"query": json.dumps(query)}


def generate_team_variables(team):
    if isinstance(team, dict):
        topic_id = re.sub(r'\W+', '', team.get("topic_id", None))
        team_name = re.sub(r'\W+', '', team.get("name", None))
        return team_name, topic_id
    return None, None


@XBlock.wants("user")  # pylint: disable=too-many-ancestors, too-many-instance-attributes
@XBlock.wants("settings")
class RocketChatXBlock(XBlock, XBlockWithSettingsMixin, StudioEditableXBlockMixin):
    """
    This class allows to embed a chat window inside a unit course
    and set the necessary variables to config the rocketChat enviroment
    """
    display_name = String(
        display_name=_("Display Name"),
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
        display_name=_("Specific Channel"),
        scope=Scope.content,
        help=_("This field allows to select the channel that would be accesible in the unit"),
        values_provider=lambda self: self.get_groups(),
    )

    ui_is_block = Boolean(
        default=False,
        scope=Scope.user_state,
        help="This is the flag for the initial channel",
    )

    selected_view = String(
        display_name=_("Select Channel"),
        default=_("Main View"),
        scope=Scope.content,
        help=_("This field allows to select the channel that would be accesible in the unit"),
        values_provider=lambda self: self.channels_enabled(),
    )

    team_channel = String(
        default="",
        scope=Scope.user_state
    )

    emoji = String(
        display_name=_("Emoji to grade with"),
        default="",
        scope=Scope.settings,
        help=_("Select the emoji which you want to grade"),
    )

    oldest = DateTime(
        display_name=_("Date From"),
        default=None,
        scope=Scope.settings,
        help=_("ISO-8601 formatted string representing the start date of this assignment.")
    )

    latest = DateTime(
        display_name=_("Date To"),
        default=None,
        scope=Scope.settings,
        help=_("ISO-8601 formatted string representing the due date of this assignment.")
    )

    target_reaction = Integer(
        display_name=_("Target Reaction Count"),
        default=5,
        scope=Scope.settings,
        help=_("Target value in order to achieve a defined grade.")
    )

    graded_activity = Boolean(
        display_name=_("Graded Activity"),
        default=False,
        scope=Scope.settings,
    )

    points = Float(
        display_name=_("Score"),
        help=_("Defines the number of points each problem is worth. "),
        values={"min": 0, "step": .1},
        default=1,
        scope=Scope.settings
    )

    grade = Float(
        scope=Scope.user_state,
        default=0
    )

    count_messages = Integer(
        display_name=_("Last Messages"),
        default=1000,
        scope=Scope.settings,
        help=_("The amount of messages to retrieve")
    )

    has_score = graded_activity
    team_view = True
    _api_teams = None
    _api_rocket_chat = None

    VIEWS = ["Main View", "Team Discussion", "Specific Channel"]

    # Possible editable fields
    editable_fields = (
        'selected_view',
        'default_channel',
        'graded_activity',
        'emoji',
        'target_reaction',
        'oldest',
        'latest',
        'points',
        'count_messages'
    )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        # pylint: disable=no-self-use
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    @XBlock.supports('multi_device')  # Mark as mobile-friendly
    def student_view(self, context=None):
        """
        The primary view of the RocketChatXBlock, shown to students
        when viewing courses.
        """
        in_studio_runtime = hasattr(
            self.xmodule_runtime, 'is_author_mode')  # pylint: disable=no-member

        if in_studio_runtime:
            return self.author_view(context)

        context = {
            "response": self.init(),
            "user_data": self.user_data,
            "ui_is_block": self.ui_is_block,
            "team_view": self.team_view,
            "public_url_service": self.server_data["public_url_service"],
            "key": hashlib.sha1("{}_{}".format(ROCKET_CHAT_DATA, self.user_data["username"])).hexdigest()
        }

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
    def api_rocket_chat(self):
        """
        Creates an ApiRocketChat object
        """
        if not self._api_rocket_chat:
            try:
                user = self.xblock_settings["admin_user"]
                password = self.xblock_settings["admin_pass"]
            except KeyError:
                LOG.exception("The admin's settings has not been found")
                raise
            self._api_rocket_chat = ApiRocketChat(  # pylint: disable=attribute-defined-outside-init
                user,
                password,
                self.server_data["private_url_service"]
            )

            LOG.info("Api rocketChat initialize: %s ", self._api_rocket_chat)

        return self._api_rocket_chat

    @property
    def api_teams(self):
        """
        Creates an ApiTeams object
        """
        if not self._api_teams:
            try:
                client_id = self.xblock_settings["client_id"]
                client_secret = self.xblock_settings["client_secret"]
            except KeyError:
                raise

            server_url = settings.LMS_ROOT_URL

            self._api_teams = ApiTeams(  # pylint: disable=attribute-defined-outside-init
                client_id,
                client_secret,
                server_url
            )

            LOG.info("Api Teams initialize: %s ", self._api_teams)

        return self._api_teams

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
    def user_data(self):
        """
        This method initializes the user's parameters
        """
        runtime = self.runtime  # pylint: disable=no-member
        user = runtime.service(self, 'user').get_current_user()
        user_data = {}
        user_data["email"] = user.emails[0]
        user_data["role"] = runtime.get_user_role()
        user_data["course_id"] = runtime.course_id
        user_data["username"] = user.opt_attrs['edx-platform.username']
        user_data["anonymous_student_id"] = runtime.anonymous_student_id
        return user_data

    @property
    def xblock_settings(self):
        """
        This method allows to get the xblock settings
        """
        return self.get_xblock_settings()

    @property
    def course_id(self):
        """
        This method allows to get the course_id
        """
        try:
            return re.sub('[^A-Za-z0-9]+', '', unicode(self.xmodule_runtime.course_id))
        except AttributeError:
            course_id = unicode(self.runtime.course_id)
            return re.sub('[^A-Za-z0-9]+', '', course_id.split("+branch", 1)[0])

    def channels_enabled(self):
        """
        This method returns a list with the channel options
        """
        if self._teams_is_enabled():
            return self.VIEWS
        view = list(self.VIEWS)
        view.remove(self.VIEWS[1])
        return view

    def get_groups(self):
        """
        This method lists the existing groups
        """
        # the following instructions get all the groups
        # except the team groups and specific teams
        course = self.course_id
        kwargs = generate_query_dict(course)
        groups = [group.split("__", 1)[0] for group in self.api_rocket_chat.get_groups(**kwargs)]

        kwargs = generate_query_dict(course, specific_team=True)
        # This instruction adds the string "(Team Group)" if the group is in team_groups
        groups += [
            '{}-{}'.format("(Team Group)", team_group.split("__", 1)[0])
            for team_group in self.api_rocket_chat.get_groups(**kwargs)
        ]

        groups.append("")
        return sorted(groups)

    def init(self):
        """
        This method initializes the user's variables and
        log in to rocketchat account
        """

        user_data = self.user_data

        response = self._login(user_data)
        if response['success']:
            response = response['data']
            user_id = response['userId']
            auth_token = response['authToken']

            response['default_group'] = self._join_user_to_groups(user_id, user_data, auth_token)
            self._update_user(user_id, user_data)

            self._grading_discussions(response['default_group'])
            return response

        return response['errorType']

    def _login(self, user_data):
        """
        This method allows to get the user's authToken and id
        or creates a user to login in RocketChat
        """
        api = self.api_rocket_chat

        rocket_chat_user = api.search_rocket_chat_user(user_data["username"])
        LOG.info("Login method: result search user: %s", rocket_chat_user["success"])

        key = hashlib.sha1("{}_{}".format(ROCKET_CHAT_DATA, user_data["username"])).hexdigest()
        data = cache.get(key)

        if data:
            return data
        elif rocket_chat_user['success']:
            data = api.create_token(user_data["username"])
        else:
            response = api.create_user(user_data["anonymous_student_id"], user_data[
                "email"], user_data["username"])
            LOG.info("Login method: result create user : %s", response)

            data = api.create_token(user_data["username"])

        LOG.info("Login method: result create token: %s", data)
        cache.set(key, data, CACHE_TIMEOUT)
        return data

    def _add_user_to_course_group(self, user_id):
        """
        This method add the user to the default course channel
        """
        group_name = "{}__{}".format(_("General"), self.course_id)
        self._add_user_to_group(
            user_id,
            group_name,
            members=[self.user_data["username"]],
            custom_fields=generate_custom_fields(course=self.course_id),
            create=True
        )

    def _add_user_to_default_group(self, group_name, user_id):
        """
        """
        group = "{}__{}".format(group_name, self.course_id)
        result = self._add_user_to_group(user_id, group)
        return result, group

    def _add_user_to_team_group(self, user_id, username, auth_token):
        """
        Add the user to team's group in rocketChat
        """
        team = self._get_team(username)

        if team is None:
            self._remove_user_from_group(self.team_channel, user_id, auth_token)
            return False
        team_name, topic_id = generate_team_variables(team)
        group_name = "{}__{}__{}".format(team_name, topic_id, self.course_id)

        if self.team_channel != group_name:
            self._remove_user_from_group(self.team_channel, user_id, auth_token)

        self.team_channel = group_name

        return self._add_user_to_group(
            user_id,
            group_name,
            members=[username],
            custom_fields=generate_custom_fields(self.course_id, team),
            create=True
        )

    def _get_team(self, username):
        """
        This method gets the user's team
        """
        team = self.api_teams.get_user_team(self.runtime.course_id, username)
        LOG.info("Get Team response: %s", team)
        if team:
            return team[0]
        return None

    def _join_user_to_groups(self, user_id, user_data, auth_token):
        """
        This method add the user to the different channels
        """
        default_channel = self.default_channel

        if self.selected_view == self.VIEWS[1] and self._teams_is_enabled():
            self.team_view = self._add_user_to_team_group(user_id, user_data["username"], auth_token)
            self.ui_is_block = self.team_view
            return self.team_channel

        elif self.selected_view == self.VIEWS[2] and default_channel:
            if default_channel.startswith("(Team Group)"):
                return self._join_user_to_specific_team_group(user_id, user_data, default_channel)

            self.ui_is_block, default_channel = self._add_user_to_default_group(default_channel, user_id)
            return default_channel
        else:
            self.ui_is_block = False
            self._add_user_to_course_group(user_id)
        return None

    def _add_user_to_group(self, user_id, group_name, **kwargs):
        """
        This method allows to add a user to any channel, returns True if it's successful
        """
        group = self.api_rocket_chat.search_rocket_chat_group(group_name)
        response = {}

        if group["success"]:
            response = self.api_rocket_chat.add_user_to_group(user_id, group['group']['_id'])
        elif kwargs.get("create", False):
            response = self.api_rocket_chat.create_group(
                group_name,
                kwargs.get("members", []),
                **kwargs.get("custom_fields", {})
            )

        return response.get("success", False)

    def _join_user_to_specific_team_group(self, user_id, user_data, default_channel):
        team = self._get_team(user_data["username"])
        if team is None:
            self.team_view = False
            return None
        default_channel = self._create_team_group_name(
            team,
            default_channel.replace("(Team Group)-", ""),
            self.course_id
        )
        self.ui_is_block = self._add_user_to_group(
            user_id,
            default_channel,
            members=[user_data["username"]],
            custom_fields=generate_custom_fields(self.course_id, team),
            create=True
        )
        return default_channel

    def _teams_is_enabled(self):
        """
        This method verifies if teams are available
        """
        from openedx_dependencies import modulestore  # pylint: disable=relative-import
        try:
            course_id = self.runtime.course_id  # pylint: disable=no-member
        except AttributeError:
            return False

        course = modulestore().get_course(course_id, depth=0)
        teams_configuration = course.teams_configuration
        LOG.info("Team is enabled result: %s", teams_configuration)
        if "topics" in teams_configuration and teams_configuration["topics"]:
            return True

        return False

    def _update_user(self, user_id, user_data):
        """
        This method updates the email and photo's profile
        """
        api = self.api_rocket_chat
        if user_data["email"] != self.email:
            self.email = api.update_user(user_id, user_data["email"])

        api.set_avatar(user_data["username"], self._user_image_url())

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

    @XBlock.json_handler
    def create_group(self, data, suffix=""):
        """
        This method allows to create a group
        """
        # pylint: disable=unused-argument
        group_name = data.get("groupName", None)

        if group_name == "" or group_name is None:
            return {"success": False, "error": "Group Name is not valid"}

        group_name = re.sub(r'\W+', '', group_name)
        specific_team = False
        members = []
        team = None

        if data.get("asTeam"):
            group_name = "{}__{}".format(group_name, self.course_id)
            specific_team = True

        elif data.get("teamGroup"):
            team = self._get_team(self.user_data["username"])
            members = list(self.get_team_members(team))
            group_name = self._create_team_group_name(team, group_name, self.course_id)

        else:
            group_name = "{}__{}".format(group_name, self.course_id)

        custom_fields = generate_custom_fields(self.course_id, team, specific_team)
        group = self.api_rocket_chat.create_group(group_name, members, **custom_fields)

        if "group" in group:
            group_id = group["group"]["_id"]

            self.api_rocket_chat.set_group_description(group_id, data.get("description"))
            self.api_rocket_chat.set_group_topic(group_id, data.get("topic"))

        LOG.info("Method Public Create Group: %s", group)
        return group

    @staticmethod
    def _create_team_group_name(team, group_name, course):

        team_name, team_topic = generate_team_variables(team)
        return "{}__{}__{}__{}".format(group_name, team_name, team_topic, course)

    def _remove_user_from_group(self, group_name, user_id, auth_token=None):
        """
        This method removes a user form a team
        """
        if not group_name:
            return False
        api = self.api_rocket_chat

        if group_name.startswith("Team-") and auth_token is not None:
            regex = group_name.replace('Team-', '', 1)
            query = {"name": {"$regex": regex}}
            kwargs = {"query": json.dumps(query)}
            groups = api.list_all_groups(user_id, auth_token, **kwargs)

            if groups["success"]:
                groups = groups["groups"]
                for group in groups:
                    api.kick_user_from_group(user_id, group["_id"])
                return {"success": True}

        group = api.search_rocket_chat_group(group_name)
        if group["success"]:
            group = group["group"]
            response = api.kick_user_from_group(user_id, group["_id"])
            return response
        return {"success": False, "error": "Channel not found"}

    def get_team_members(self, team):
        """
        This method allows to get the members of a team
        """
        if team:
            team_id = team["id"]
            members = self.api_teams.get_members(team_id)
            if members:
                for member in members:
                    yield member["user"]["username"]

    @XBlock.json_handler
    def leave_group(self, data, suffix=""):
        """
        This method allows to leave a group
        """
        # pylint: disable=unused-argument

        username = self.user_data["username"]
        user = self.api_rocket_chat.search_rocket_chat_user(username)
        group_name = data["groupName"]

        if not user["success"]:
            return {"success": False, "error": "User is not valid"}

        if group_name == "" or group_name is None:
            return {"success": False, "error": "Group Name is not valid"}

        team = self._get_team(self.user_data["username"])
        team_name, topic_id = generate_team_variables(team)

        if group_name == team_name or group_name == _("General"):
            return {"success": False, "error": "You Can Not Leave a Main Group"}
        group_name = "{}__{}__{}__{}".format(group_name, team_name, topic_id, self.course_id)

        return self._remove_user_from_group(group_name, user["user"]["_id"])

    @XBlock.json_handler
    def get_list_of_groups(self, data, suffix=""):
        """Returns a list with the group names"""
        # pylint: disable=unused-argument
        user_id = data.get("userId", None)
        auth_token = data.get("authToken", None)

        if not user_id or not auth_token:
            LOG.warn("Invalid data for method get_list_of_groups: %s", data)
            return None

        team = self._get_team(self.user_data["username"])

        kwargs = generate_query_dict(self.course_id, team=team)

        groups = list(self._get_list_groups(user_id, auth_token, **kwargs))
        return groups

    def _get_list_groups(self, user_id, auth_token, **kwargs):
        """
        This method allows to get a list of group names
        """
        api = self.api_rocket_chat
        groups = api.list_all_groups(user_id, auth_token, **kwargs)
        if groups["success"]:
            groups = groups["groups"]
            for group in groups:
                yield group["name"]

    def _get_user_messages(self, group_name, latest="", oldest="", count=100):
        """
        Gets the messages from a user's private group.
        """
        api = self.api_rocket_chat
        rocket_chat_group = api.search_rocket_chat_group(group_name)

        if not rocket_chat_group['success']:
            return []

        group_id = rocket_chat_group['group']['_id']
        messages = api.get_groups_history(room_id=group_id, latest=latest,
                                          oldest=oldest, count=count)

        if not messages["success"]:
            return []

        return [message for message in messages["messages"]
                if message["u"]["username"] == self.user_data["username"]]

    def _filter_by_reaction_and_user_role(self, messages, reaction):
        """
        Returns generator with filtered messages by a given reaction
        """
        for message in messages:
            if reaction not in message.get("reactions", {}):
                continue
            usernames = message["reactions"][reaction]["usernames"]

            for username in usernames:
                if self._validate_user_role(username):
                    yield message
                    break

    def _validate_user_role(self, username):
        """
        Returns True if the user is privileged in teams discussions for
        this course.
        """
        from openedx_dependencies import CourseStaffRole  # pylint: disable=relative-import

        user = User.objects.get(username=username)

        if user.is_staff:
            return True
        if CourseStaffRole(self.user_data["course_id"]).has_user(user):
            return True
        return False

    def _grading_discussions(self, graded_group):
        """
        This method allows to grade contributions to Rocket.Chat given a reaction.
        """
        if not self.graded_activity or self.grade == self.points:
            return
        messages = self._get_user_messages(graded_group,
                                           self.latest, self.oldest, self.count_messages)
        messages = list(self._filter_by_reaction_and_user_role(messages, self.emoji))
        if len(messages) >= self.target_reaction:
            self.grade = self.points
            self.runtime.publish(self, 'grade', {'value': self.grade, 'max_value': self.points})

    def max_score(self):
        if self.graded_activity:
            return self.points

    @XBlock.handler
    def logout_user(self, request=None, suffix=None):
        """
        This method allows to invalidate the user token
        """
        # pylint: disable=unused-argument
        key = request.GET.get("beacon_rc")
        data = cache.get(key)
        if data:
            api = self.api_rocket_chat
            user_data = data.get("data")
            login_token = user_data.get("authToken")
            user_id = user_data.get("userId")
            response = api.logout_user(user_id, login_token)

            if response.get("status") == "success":
                cache.delete(key)
                return Response(status=202)

        return Response(status=404)
