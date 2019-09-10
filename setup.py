"""Setup for rocketc XBlock."""

import os

from setuptools import setup

__version__ = '0.4.1'


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name='rocketc-xblock',
    version=__version__,
    description='rocketc XBlock',   # TODO: write a better description.
    license='UNKNOWN',          # TODO: choose a license: 'AGPL v3' and 'Apache 2.0' are popular.
    packages=[
        'rocketc',
    ],
    install_requires=[
        'XBlock',
        'rocketchat-API==0.6.34',
    ],
    entry_points={
        'xblock.v1': [
            'rocketc = rocketc:RocketChatXBlock',
        ]
    },
    package_data=package_data("rocketc", ["static", "public"]),
)
