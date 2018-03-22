from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers

from rocketChat.views import RocketChatView


urlpatterns = [
    url(r'^login', RocketChatView),
    url(r'^admin/', admin.site.urls),
]