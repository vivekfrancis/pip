import re
import sys
import textwrap
from doctest import OutputChecker, ELLIPSIS
from test_pip import pyversion, reset_env, run_pip, write_file


distribute_re = re.compile(r'^distribute==[0-9.]+ \(CURRENT: [0-9.]+ LATEST: [0-9.]+\)\n', re.MULTILINE)


def _check_output(result, expected):
    checker = OutputChecker()
    actual = str(result)

    ## FIXME!  The following is a TOTAL hack.  For some reason the
    ## __str__ result for pkg_resources.Requirement gets downcased on
    ## Windows.  Since INITools is the only package we're installing
    ## in this file with funky case requirements, I'm forcibly
    ## upcasing it.  You can also normalize everything to lowercase,
    ## but then you have to remember to upcase <BLANKLINE>.  The right
    ## thing to do in the end is probably to find out how to report
    ## the proper fully-cased package name in our error message.
    if sys.platform == 'win32':
        actual = actual.replace('initools', 'INITools')

    # This allows our existing tests to work when run in a context
    # with distribute installed.
    actual = distribute_re.sub('', actual)

    def banner(msg):
        return '\n========== %s ==========\n' % msg
    assert checker.check_output(expected, actual, ELLIPSIS), banner('EXPECTED')+expected+banner('ACTUAL')+actual+banner(6*'=')


def test_list_command():
    """
    Test default behavior of list command.

    """
    reset_env()
    run_pip('install', 'INITools==0.2', 'simplejson==2.0.0')
    result = run_pip('list')
    expected = textwrap.dedent("""\
        Script result: pip list
        -- stdout: --------------------
    """)
    if pyversion < (3,):
        expected += textwrap.dedent("""\
        wsgiref (...)
        initools (0.2)
        simplejson (2.0.0)
        """)
    else:
        expected += textwrap.dedent("""\
        initools (0.2)
        simplejson (2.0.0)
        """)
    _check_output(result, textwrap.dedent(expected))


def test_outdated_default():
    """
    Test the behavior of --outdated option in the list command

    """

    env = reset_env()
    total_re = re.compile('LATEST: +([0-9.]+)')
    write_file('initools-req.txt', textwrap.dedent("""\
        INITools==0.2
        # and something else to test out:
        simplejson==2.0.0
        """))
    run_pip('install', '-r', env.scratch_path/'initools-req.txt')
    result = run_pip('search', 'simplejson')
    simplejson_ver = total_re.search(str(result)).group(1)
    result = run_pip('search', 'INITools')
    initools_ver = total_re.search(str(result)).group(1)
    result = run_pip('list', '--outdated', expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: pip list --outdated
        -- stdout: --------------------
        initools (CURRENT: 0.2 LATEST: %s)
        simplejson (CURRENT: 2.0.0 LATEST: %s)
        """ % (initools_ver, simplejson_ver))
    _check_output(result, expected)
