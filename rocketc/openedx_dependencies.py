"""
OpenEdx dependencies
"""
# pylint: disable=import-error
# pylint: disable=unused-import
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_urls_for_user
from xmodule.modulestore.django import modulestore
from student.roles import CourseStaffRole
