import requests
import json

from django.shortcuts import render
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt

from models import RocketChat
from serializers import RocketChatSerializer 

from rest_framework.response import Response
from django.http import JsonResponse

@csrf_exempt
def RocketChatView(request):

    """A function to read the version of Rocketchat"""
    headers = {'content-type': 'application/json'}
    data = { "username": "andrey92", "password": "edunext" }
    url = "http://localhost:3000/api/v1/login"
    r = requests.post(url, json=data, headers=headers)   
    response = r.json()
    token = response['data']['authToken']
    re = {"loginToken":token}
    return JsonResponse(re, status=201)
       
