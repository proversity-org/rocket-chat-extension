"""
Api for teams
"""
import os
import logging
import requests
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session

LOG = logging.getLogger(__name__)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class ApiTeams(object):  #pylint: disable=too-few-public-methods

    headers = {}
    API_PATH = 'api/team/v0'

    def __init__(self, username, password, client_id, client_secret,  # pylint: disable=too-many-arguments
                 server_url='http://127.0.0.1:8000'):
        """Creates a ApiTeams object"""
        self.server_url = server_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.password = password
        self.username = username
        self.headers["Authorization"] = "{} {}".format(
            "Bearer", self._get_token(server_url))

    def _get_token(self, server_url):
        """This method get the Authorization token"""
        client_id = self.client_id
        client_secret = self.client_secret

        oauth = OAuth2Session(
            client=LegacyApplicationClient(client_id=client_id))
        token_url = "/".join([server_url, "oauth2/access_token/"])

        token = oauth.fetch_token(token_url=token_url,
                                  client_id=client_id,
                                  client_secret=client_secret,
                                  username=self.username,
                                  password=self.password)

        LOG.info("The acces token is: %s", token["access_token"])

        return token['access_token']

    def _call_api_get(self, url_path):
        """This method return the response"""
        url = "/".join([self.server_url, self.API_PATH, url_path])
        return requests.get(url, headers=self.headers)

    def get_user_team(self, course_id, username):
        """Get the user's team"""
        course_id = course_id.to_deprecated_string().replace("+", "%2B")
        url_path = "teams/?course_id={}&username={}".format(
            course_id, username)
        team_request = self._call_api_get(url_path)

        if team_request.status_code == 200:
            return team_request.json()["results"]
        return team_request.json()
