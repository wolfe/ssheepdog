import os
import sys
from fabric.operations import local
from fabric.colors import red

PROJECT_NAME = 'ssheepdog'
APPS = ['ssheepdog']
TESTS = ' '.join(APPS)


def test():
    """
    Run unit tests for this Django Application
    """
    if len(APPS) == 0:
        return
    local('./manage.py test %s' % TESTS)


def freeze():
    """
    Generate a stable requirements.txt based on requirements.spec.txt.
    """
    local('pip freeze -r requirements.spec.txt > requirements.txt')


try:
    assert os.getcwd() == os.path.dirname(os.path.abspath(__file__))
except AssertionError:
    print red('You must run this from the root of the project.')
    sys.exit(1)
