import os
import subprocess
import sys

import argparse
from lib.commands.commands import arg

from . import cli
from . import config


# Utilities
# ---------
from contextlib import contextmanager


@contextmanager
def push_sys_path(path):
  sys.path.insert(0, path)
  yield
  sys.path.pop(0)


def _in_project():
  return config.PROJECT_PATH != config.HOME_PATH


def activate_virtualenv(path):
  activate_this = os.path.join(path, 'venv', 'bin', 'activate_this.py')
  execfile(activate_this, dict(__file__=activate_this))


def _execute_django_command(name=None, args=None):
  args = args or []
  name = name or 'help'

  activate_virtualenv(config.PROJECT_PATH)
  try:
    from django.core.management import execute_from_command_line
  except ImportError:
    cmd = ' '.join([str(arg) for arg in args])
    print 'Not in a Django project.  Did not run command: %s' % cmd
    return

  argv = ['manage.py', name] + args
  with push_sys_path(config.PROJECT_PATH):
    execute_from_command_line(argv)


# Commands to move somewhere else
# ===============================

# TODO(nick): Not really a Django command.  Move this somewhere else!
def test():
  """Run tests and linters."""
  # lint: from main.py  # TODO(nick): Move this into a library!
  if _in_project():
    subprocess.call(['flake8', config.PROJECT_PATH])
  # end lint
  _execute_django_command('test')
cli.register(test)


# TODO(nick): Not really a Django command.  Move this somewhere else!
def shell():
  """Run shell."""
  _execute_django_command('shell_plus')
cli.register(shell)


# Django Commands
# ===============

@arg('name', nargs='?',
     help="The name of the manage.py command you want to run.")
@arg('args', nargs=argparse.REMAINDER,
     help="Arguments to pass to the manage.py command.")
def m(name, args):
  """Run manage.py commands (using the dev environment settings)."""
  _execute_django_command(name, args)
cli.register(m)


# TODO(nick): This should be a `run *` command that can run other things too.
def runserver():
  """Run the development server and restart on crash."""
  try:
    subprocess.call('\n'.join(['while true; do',
                               '  # re-start service',
                               '  echo "Starting Django Server"',
                               '  python manage.py runserver',
                               '  sleep 2',
                               'done']),
                    shell=True)
  except KeyboardInterrupt:
    pass
cli.register(runserver)


def migrate():
  """Make migrations and run them."""
  _execute_django_command('makemigrations')
  _execute_django_command('migrate')
cli.register(migrate)


def clear_cache():
  """Clear expired session data from the database-backed cache."""
  print 'Clearing database cache...'
  _execute_django_command('clearsessions')
cli.register(clear_cache, name='clear-cache')