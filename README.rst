Xblock RocketChat |build-status| |coverage-status| |codacy-status|
===================================================================

RocketChat Xblock generates a view that uses the rocketChat ui allowing the user communicate in real time. An overview of its features is the following:

    - This creates a rocketchat-user with the platform-user information.
    - Login a user in rocketchat is automatic.(This uses a script on rocketchat configuration)
    - Rocketchat-user and platform-user have the same username and profile picture.
    - Always is created a channel for the course.
    - All the created channels are private.


Requirements
-------------
- RocketChat Server. You need your own instance of configured rocketChat running on your local machine (for local development) or on your production server.

Installation
------------

Devstack installation (for local development)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Install the requirements into the Python virtual environment of your `edx-platform` installation by running the following command from the root folder:

```
$ pip install  -e .
```

Production installation
^^^^^^^^^^^^^^^^^^^^^^^
Create a branch of edx-platform to commit a few minor changes:

Add rocketChat xblock to the platform requirements
**************************************************
    In ```requirements/edx/github.txt```, add:

    ```git+https://github.com/proversity-org/rocket-chat-extension.git@v0.2.12#egg=rocketc-xblock==0.2.12```

Required Configurations
-----------------------

Admin Level
^^^^^^^^^^^
1. Go to http://your-platform-domain/admin/oauth2/client/
2. Click on "Add Client"
3. Complete the required fields.
4. Click on "Save and continue"
5. Copy client_id and client_secret fields.

Platform Level
^^^^^^^^^^^^^^
1. Add in the settings (lms and cms) the following:

    ```
    XBLOCK_SETTINGS = {
    'RocketChatXBlock': {
    'private_url_service': 'rocket_chat_private_url',
    'public_url_service': 'rocket_chat_public_url',
    'admin_user': 'admin_rocket_chat',
    'admin_pass': 'pass_admin',
    'username':'user_staff',
    'password':'password_staff",
    'client_id': 'clientet_id_staff',
    'client_secret':'client_secret_staff'
    }}
    ```

- private_url_service = It is the rocketChat server private url(If you don't have it you can use the public url).
- public_url_service = It is the public rocketChat url.
- admin_user = It is a rocketChat user with admin permissions.
- admin_pass = It is the admin_user password.
- username = It is user's username who was used to create the client in Admin Level
- password = It is the user's password who was used to create the client in Admin Level
- client_id = The client_id copied in Admin Level
- client_secret = The client_secret copied in Admin Level



RocketChat Server Level
^^^^^^^^^^^^^^^^^^^^^^^
1. Administration ⇒ Layout ⇒ CustomScripts and add the following:

    ``"use strict";``

    ``var url_string, url, auth_token, user_id;``

    ``url_string = window.location.href;``

    ``url = new URL(url_string);``

    ``auth_token = url.searchParams.get("authToken");``

    ``user_id = url.searchParams.get("userId");``

    ``if (auth_token !== null && user_id !== null) {``

        ``localStorage.setItem("Meteor.loginToken", auth_token);``

        ``localStorage.setItem("Meteor.userId", user_id);``

    ``} else {``

        ``console.warn("Some parameters are missing. Please provide them");``

    ``}``

2. Administration ⇒ Layout ⇒CustomCSS (optional if you don't want to see logout button)

    ``li[data-id='logout'] {``

        ``display: none;``

    ``}``

3.  Administration ⇒ Accounts set False (Optional)

        Allow User Profile Change

        Allow User Avatar Change

        Allow Name Change

        Allow Username Change

        Allow Email Change

        Allow Password Change

4. Administration ⇒ Accounts ⇒ Registration set False (Optional)

  Use Default Blocked Domains List


Course Authoring in edX Studio
-------------------------------

1. Change Advanced Settings

    1. Open a course you are authoring and select "Settings" ⇒ "Advanced
       Settings
    2. Navigate to the section titled "Advanced Module List"
    3. Add "rocketc" to module list.
    4. Click on "Save Changes".

2. Create a Rocket Chat XBlock

    1. Return to the Course Outline
    2. Create a Section, Sub-section and Unit, if you haven't already
    3. In the "Add New Component" interface, you should now see an "Advanced" button
    4. Click "Advanced" and choose "Rocket Chat Xblock"

Features include
----------------
This features can be set in studio (EDIT Button).

Select Channel
^^^^^^^^^^^^^^

- **Main View:** This option allows to see all the channels where a user is, you can switch channels and use the rocketchat user interface options.

- **Team Discussion:** If you are a team's member you will see a specific channel for that team, if you are not a team's member you will get a message to encourage joining to a team.(Only available if teams are activated)

- **Specific Channel:** Show only the channel selected in default channel.

Default Channel
^^^^^^^^^^^^^^^
- A list with the possibles channels. If you selected Specific Channel in Select Channel field you will see the embedded view with the channel selected in this option.

Create Group
^^^^^^^^^^^^
You can create a private group to select in the option "Default Channel".

- Group Name: A required field. It is the name for the channel you want to create.
- Description: Optional. A short description clarifying the channel's goal.
- Topic: Optional. What will you talk about ?.

About this xblock
-----------------

The RocketChat Xblock was built by `eduNEXT <https://www.edunext.co>`_, a company specialized in open edX development and open edX cloud services.



How to contribute
-----------------

* Fork this repository.
* Commit your changes on a new branch
* Make a pull request to the master branch
* Wait for the code review and merge process

.. |build-status| image:: https://circleci.com/gh/proversity-org/rocket-chat-extension.svg?style=svg
   :target: https://circleci.com/gh/proversity-org/rocket-chat-extension
   :alt: CircleCI build status
.. |coverage-status| image::  https://codecov.io/gh/eduNEXT/rocket-chat-extension/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/eduNEXT/rocket-chat-extension
   :alt: Coverage badge
.. |codacy-status| image:: https://api.codacy.com/project/badge/Grade/31f24686b01944ac835ef835a6ce32bb
   :target: https://www.codacy.com/app/andrey-canon/rocket-chat-extension
   :alt: Codacy badge
