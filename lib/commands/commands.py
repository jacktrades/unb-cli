'''
A decorator-based API to argparse for easy creation of subcommands.


Example:

    from commands import Group, arg

    register = Group()

    @arg('-n', '--num', type=int, default=42)
    def echo(args):
      """Usage: %(prog)s echo [-n, --num]=<int>"""
      print "Arguments: ", args
    register.command(echo)

    if __name__ == '__main__':
      register.dispatch()


For a more in-depth example, see the example.py file.


TODO(nick): Look into providing completions:
              https://github.com/kislyuk/argcomplete

TODO(nick): Write some tests!
'''

import argparse
import sys
import textwrap


def arg(*args, **kwargs):
  """Annotate a function by adding an Argparse arg to the meta-data.

  This appends an Argparse "argument" to the function's ``ARGPARSE_ARGS_LIST``
  attribute, creating ``ARGPARSE_ARGS_LIST`` if it does not already exist.
  Aside from that, it returns the decorated function unmodified, and unwrapped.

  The "arguments" are simply ``(args, kwargs)`` tuples which will be passed to
  the parser created from the function as
  ``parser.add_argument(*args, **kwargs)``.

  Args:

    name/flags -  Either a name or a list of (positional) option strings,
                  e.g. ('foo') or ('-f', '--foo').
    action     -  The basic type of action to be taken when this argument is
                  encountered at the command line.
    nargs      -  The number of command-line arguments that should be
                  consumed.
    const      -  A constant value required by some action and nargs
                  selections.
    default    -  The value produced if the argument is absent from the
                  command line.
    type       -  The type to which the command-line argument should be
                  converted.
    choices    -  A container of the allowable values for the argument.
    required   -  Whether or not the command-line option may be omitted
                  (optionals only).
    help       -  A brief description of what the argument does.
    metavar    -  A name for the argument in usage messages.
    dest       -  The name of the attribute to be added to the object
                  returned by parse_args().


  Example:

      @arg('-n', '--num', type=int, default=42)
      @arg('-s', '--some-switch', action='store_false')
      def command_name(args):
        print 'args: ', args


  Also see:

    [argparse.add_argument](
      https://docs.python.org/2/library/argparse.html#the-add-argument-method)
  """
  def annotate(func):
    # Get the list of argparse args already added to func (if any).
    argparse_args_list = getattr(func, 'ARGPARSE_ARGS_LIST', [])
    argparse_args_list.insert(0, (args, kwargs))
    setattr(func, 'ARGPARSE_ARGS_LIST', argparse_args_list)
    return func
  return annotate


class Group(object):
  """A collection of (sub)commands."""

  FORMATTER_CLASS = argparse.RawDescriptionHelpFormatter
  """Set the help text formatter class to use for the Group.

  Argparse default formatters include:

      argparse.RawDescriptionHelpFormatter
      argparse.RawTextHelpFormatter
      argparse.ArgumentDefaultsHelpFormatter

  Also see: https://docs.python.org/2/library/argparse.html#formatter-class
  """

  REPLACE_UNDERSCORES_WITH_DASHES = False
  """If True, replace underscores with dashes in function name.

  This is done only if the `name` option is not given. (defaults to False).
  """

  def __init__(self,
               init_func=None,
               replace_underscores_with_dashes=None,
               formatter_class=None,
               description='',
               title='',
               epilog=''):
    self._init_func = init_func

    self.title = title or 'Commands'
    self.description = description
    self.epilog = epilog

    if replace_underscores_with_dashes is not None:
      self.REPLACE_UNDERSCORES_WITH_DASHES = replace_underscores_with_dashes
    if formatter_class is not None:
      self.FORMATTER_CLASS = formatter_class

    # Create the argparse group and subparsers list.
    self.group = argparse.ArgumentParser(
      formatter_class=self.FORMATTER_CLASS,
      description=description,
    )
    self.subparsers = self.group.add_subparsers(
      title=self.title,
      metavar='',
    )
    self.subparsers_registry = {}

  def __call__(self, *args):
    """Invoke as a CLI or by directly calling an instance of Group."""
    if not args:
      args = sys.argv

    return self.dispatch(args)

  def _get_name(self, func, name=None):
    """Return the command name."""
    if name:
      return name
    if self.REPLACE_UNDERSCORES_WITH_DASHES:
      return func.__name__.replace('_', '-')
    return func.__name__

  def _parse_doc(self, doc):
    parts = {
      'title': '',
      'body': '',
    }
    if not doc:
      return parts
    sp = doc.split('\n', 1)
    parts['title'] = sp[0].strip()
    if len(sp) > 1:
      parts['body'] = textwrap.dedent(sp[1]).strip()
    return parts

  def register(self, handler, name=None, doc=None):
    """Register a handler for a command(name).

    Args:
      handler: Command handler called with parsed arguments.
      name: The command name is introspected from the handler, unless specified
        here.
    """
    handler_name = self._get_name(handler, name)
    if doc:
      doc = self._parse_doc(doc)
    else:
      doc = self._parse_doc(handler.__doc__)
    handler_ARGPARSE_ARGS_LIST = getattr(handler, 'ARGPARSE_ARGS_LIST', [])

    parser = self.subparsers.add_parser(
      handler_name,
      help=doc['title'],
      description=doc['title'],
      epilog=doc['body'],
      formatter_class=self.FORMATTER_CLASS,
    )
    for arguments in handler_ARGPARSE_ARGS_LIST:
      args, kwargs = arguments
      parser.add_argument(*args, **kwargs)
    parser.set_defaults(_handler=handler)

    # Argparse doesn't have an easy way to get a list of subparsers for a
    # group.  So we build one as we add subparsers.
    self.subparsers_registry[handler_name] = parser
    return parser

  def command(self, name=None):
    def register_wrapper(handler):
      self.register(handler, name)
      return handler
    return register_wrapper

  def add_group(self, group, name):
    """Register a subcommand parser.

    Args:
      group: An instance of Group.
      name: Name to register the Group.
    """
    # print group.epilog
    parser = self.subparsers.add_parser(
      name,
      prog='%s %s' % (self.group.prog, name),
      help=group.title,
      description=group.description,
      epilog=group.epilog,
      formatter_class=self.FORMATTER_CLASS,
    )

    parser.add_argument('args', nargs='*')
    # parser.set_defaults(_func=group.dispatch)
    parser.set_defaults(_handler=group)

    # Argparse doesn't have an easy way to get a list of subparsers for a
    # group.  So we build one as we add subparsers.
    self.subparsers_registry[name] = parser
    return parser

  def dispatch(self, args=None):
    if args is None:
      args = sys.argv
    # command_name = args[0]
    args = args[1:]

    # No args in the initial invocation should print the help message.
    if not args:
      args = ['-h']

    parsed = self.group.parse_args(args)

    handler = parsed._handler
    del parsed._handler

    if self._init_func:
      self._init_func()

    if isinstance(handler, Group):
      if not parsed.args:
        handler.group.print_help()
      else:
        handler.dispatch([args[0]] + parsed.args)
    else:
      handler(**vars(parsed))
