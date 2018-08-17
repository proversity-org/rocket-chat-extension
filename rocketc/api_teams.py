"""
Api for teams
"""
import os
import logging
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

LOG = logging.getLogger(__name__)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class ApiTeams(object):  # pylint: disable=too-few-public-methods

    API_PATH = 'api/team/v0'

    def __init__(self, client_id, client_secret,  # pylint: disable=too-many-arguments
                 server_url='http://127.0.0.1:8000'):
        """Creates a ApiTeams object"""
        self.server_url = server_url
        self. session = self._init_session(server_url, client_id, client_secret)

    @staticmethod
    def _init_session(server_url, client_id, client_secret):
        """This method get the Authorization token"""
        client = BackendApplicationClient(client_id=client_id)
        oauth = OAuth2Session(client=client)
        token_url = "/".join([server_url, "oauth2/access_token/"])
        headers = {}

        token = oauth.fetch_token(token_url=token_url,
                                  client_id=client_id,
                                  client_secret=client_secret
                                 )

        headers["Authorization"] = "{} {}".format(
            "Bearer", token['access_token'])
        session = requests.Session()
        session.headers.update(headers)
        return session

    def _call_api_get(self, url_path, payload=None):
        """This method return the response"""
        url = "/".join([self.server_url, self.API_PATH, url_path])
        return self.session.get(url, params=payload)

    def get_user_team(self, course_id, username):
        """Get the user's team"""
        course_id = course_id.to_deprecated_string()
        url_path = "teams"
        payload = {"course_id": course_id, "username": username}
        team_request = self._call_api_get(url_path, payload)

        if team_request.status_code == 200:
            return team_request.json()["results"]
        LOG.error("An error has ocurred trying to get the user with status code = %s",
                  team_request.status_code)
        return None

    def get_members(self, team_id):
        """Get the team members"""
        url_path = "team_membership"
        payload = {"team_id": team_id}
        team_request = self._call_api_get(url_path, payload)

        if team_request.status_code == 200:
            return team_request.json()["results"]
        LOG.error("An error has ocurred trying to fetch team members with status code = %s",
                  team_request.status_code)
        return None

    def get_course_teams(self, course_id):
        """Get the user's team"""
        course_id = course_id.to_deprecated_string()
        url_path = "teams"
        payload = {"course_id": course_id}
        team_request = self._call_api_get(url_path, payload)

        if team_request.status_code == 200:
            return team_request.json()["results"]
        LOG.error("An error has ocurred trying to get the user with status code = %s",
                  team_request.status_code)
        return None
