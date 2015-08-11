"""
unb
===

Overview
--------

A shell utility (``unb``) is provided to accomplish common development tasks
with the UNB project.


Installation
------------

The ``unb`` utility is meant to be installed into and run in a virtual
environment.

The following install instructions assume you have already installed the shell
utility ``unb-go``, also found in this package.

::

   unb-go
   cd management/
   pip install --editable .

After installing, the ``unb`` command will be available.


Documentation and Usage
-----------------------

The unb utility's documentation is available through the ``--help`` option.

::

   unb --help

"""

import subprocess

from lib.commands.commands import arg

from unb_cli import version
import utilities

from . import cli
from . import config


def lint():
  """Run linters.

  Note:

  If you want a catch-all configuration, add a ``~/.config/flake8`` file.
  Here's an example.  This ignores some specific errors (E111: 4 space indent
  for example), and also excludes any directory in the project named ``venv``
  or ``migrations``.

      [flake8]
      ignore=E111,E121,F403
      exclude=migrations,venv
      max-line-length = 79

  For more info: https://flake8.readthedocs.org/en/2.0/config.html
  """
  if utilities._in_project(config.PROJECT_PATH):
    subprocess.call(['flake8', config.PROJECT_PATH])
cli.register(lint)


@arg('-v',
     '--verbose',
     action='store_false',
     help="Enable verbose output.")
def install_requirements(verbose=False):
  """pip install (dev-)requirements.txt"""

  def cmd(name):
    """Build the pip install command with appropriate options."""
    command = ['pip', 'install', '-r', name]
    if not verbose:
      command = command + ['-q']
    return command

  print 'Installing project dependencies...'
  subprocess.call(cmd(config.REQUIREMENTS_FILE_PATH))
  subprocess.call(cmd(config.DEV_REQUIREMENTS_FILE_PATH))
  # TODO(nick): Install npm dependencies per frontend project.
  #   $ npm install
cli.register(install_requirements, name='install-requirements')


def get_version():
  """Get the version number of the current project."""
  v = version.read(config.VERSION_FILE_PATH)
  if v is not None:
    print v
cli.register(get_version, name='version')


@arg('part', nargs='?', default='patch')
def bump(part):
  """Bump the version number."""
  version.bump_file(config.VERSION_FILE_PATH, part, '0.0.0')
cli.register(bump)


@arg('app_name')
def update_remote(app_name):
  """Update the Heroku git remote given a Heroku app name.

  Ensure the remote is set to use the ssh protocol, which also eliminates the
  need to specify the app name for each Heroku toolbelt command.
  """
  subprocess.call(['git', 'remote', 'rm', 'heroku'])
  subprocess.call(['heroku', 'git:remote', '-a', app_name, '--ssh-git'])
cli.register(update_remote, name='update-remote')


def shell():
  """Run shell."""
  if utilities.is_django_project(config.PROJECT_PATH):
    import django_commands
    django_commands._execute_django_command('shell_plus')
  else:
    subprocess.call(['ipython'])
cli.register(shell)
