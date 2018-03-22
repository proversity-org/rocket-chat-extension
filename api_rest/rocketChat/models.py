import requests

from django.db import models

class RocketChat(models.Model):
    """
    Test class
    """
    admin_user = "andrey92"
    admin_pass = "edunext"

    def get_requests(self, url, headers=None):
        try:
            response = requests.get(url, headers=headers)




