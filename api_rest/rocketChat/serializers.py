from rest_framework import serializers
from rocketChat.models import RocketChat

class RocketChatSerializer(serializers.ModelSerializer):
    """
    """
    # data = serializers.JSONField()

    class Meta:
        model = RocketChat
        fields = ('data',)