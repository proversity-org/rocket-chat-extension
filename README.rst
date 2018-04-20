Xblock RocketChat |build-status| |coverage-status| |codacy-status|
=========================================================

RocketChat Xblock allows to implement a chat window inside a course.

Installation
------------
Add the content of login_script.js to custom scripts in rocketChat user's interface
Add the content of custom_css.css to custom css in rocketChat user's interface

Install the requirements into the Python virtual environment of your `edx-platform` installation by running the following command from the root folder:

```
$ pip install  -e .
```

Enabling in Studio
-------------------

After successful installation, you can activate this component for a
course following these steps:

* From the main page of a specific course, navigate to `Settings -> Advanced Settings` from the top menu.
* Check for the `Advanced Module List` policy key, and Add ``"rocketc"``` to the policy value list.
* Click the "Save changes" button.

Usage
-----


Common use cases
----------------


Features include
----------------


About this xblock
-----------------

The RocketChat Xblock was built by `eduNEXT <https://www.edunext.co>`_, a company specialized in open edX development and open edX cloud services.



How to contribute
-----------------

* Fork this repository.
* Commit your changes on a new branch
* Make a pull request to the master branch
* Wait for the code review and merge process

.. |build-status| image:: https://circleci.com/gh/eduNEXT/rocket-chat-extension.svg?style=svg
   :target: https://circleci.com/gh/eduNEXT/rocket-chat-extension
   :alt: CircleCI build status
.. |coverage-status| image::  https://codecov.io/gh/eduNEXT/rocket-chat-extension/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/eduNEXT/rocket-chat-extension
   :alt: Coverage badge
.. |codacy-status| image:: https://api.codacy.com/project/badge/Grade/31f24686b01944ac835ef835a6ce32bb
   :target: https://www.codacy.com/app/andrey-canon/rocket-chat-extension
   :alt: Codacy badge
