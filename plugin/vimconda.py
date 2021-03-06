""" Global code for Python 
    
    Written in python3 but should run in python2 based on Writing Python 2-3
    compatible code at http://python-future.org/compatible_idioms.html """
# vim-conda
# Version: 0.0.2
# Caleb Hattingh
# Revised by John D. Fisher
# MIT Licence

# For Python2 compatibility
from __future__ import print_function

from os.path import join, dirname #, normpath
from subprocess import check_output, PIPE

import copy
import json
import os
import sys
# TODO: Refactor to use from subprocess in functions. Currently mix of
# both
import subprocess
import vim



_conda_py_globals = dict(reset_sys_path=copy.copy(sys.path))  # Mutable global container

msg_suppress = int(vim.eval('exists("g:conda_startup_msg_suppress")'))
if msg_suppress:
    msg_suppress = int(vim.eval('g:conda_startup_msg_suppress'))

def python_input(message = 'input'):
    vim.command('call inputsave()')
    vim.command("let user_input = input('" + message + "', '	', 'custom,Conda_env_input_callback')")
    vim.command('call inputrestore()')
    return vim.eval('user_input')


def obtain_sys_path_from_env(env_path):
    """ Obtain sys.path for the selected python bin folder.
    The given `env_path` should just be the folder, not including
    the python binary. That gets added here.

    :param str env_path: The folder containing a Python.
    :return: The sys.path of the provided python env folder.
    :rtype: list """
    pyexe = os.path.join(env_path, 'python')
    args = ' -c "import sys, json; sys.stdout.write(json.dumps(sys.path))"'
    cmd = pyexe + args
    syspath_output = subprocess.check_output(cmd, shell=True,
                                             executable=os.getenv('SHELL'))\
                                             .decode('utf-8')
    # Use json to convert the fetched sys.path cmdline output to a list
    return json.loads(syspath_output)


def conda_activate(env_name, env_path, envs_root):
    """ This function performs a complete (internal) conda env
    activation. There are two primary actions:

    1. Change environment vars $PATH and $CONDA_DEFAULT_ENV

    2. Change EMBEDDED PYTHON sys.path, for jedi-vim code completion

    :return: None """
    # This calls a vim function that will
    # change the $PATH and $CONDA_DEFAULT_ENV vars
    vim.command("call s:CondaActivate('{}', '{}', '{}')".format(env_name, env_path, envs_root))
    # Obtain sys.path for the selected conda env
    # TODO: Perhaps make this flag a Vim option that users can set?
    ADD_ONLY_SITE_PKGS = True
    if ADD_ONLY_SITE_PKGS:
        new_paths = [os.path.join(env_path, 'lib', 'site-packages')]
    else:
        new_paths = obtain_sys_path_from_env(env_path)
    # Insert the new paths into the EMBEDDED PYTHON sys.path.
    # This is what jedi-vim will use for code completion.
    # TODO: There is another way we could do this: instead of a full reset, we could
    # remember what got added, and the reset process could simply remove those
    # things; this approach would preserve any changes the user makes to
    # sys.path inbetween calls to s:CondaChangeEnv()...
    # TODO: I found out that not only does jedi-vim modify sys.path for
    # handling VIRTUALENV (which is what we do here), but it also looks like
    # there is a bug in that the same venv path can get added multiple times.
    # So it looks like the best policy for now is to continue with the
    # current design.
    sys.path = new_paths + _conda_py_globals['reset_sys_path']   # Modify sys.path for Jedi completion
    if not msg_suppress:
        print('Activated env: {}'.format(env_name))


def conda_deactivate():
    """ This does the reset. """
    # Resets $PATH and $CONDA_DEFAULT_ENV
    vim.command('call s:CondaDeactivate()')
    # Resets sys.path (embedded Python)
    _conda_py_globals['syspath'] = copy.copy(sys.path)  # Remember the unmodified one
    sys.path = _conda_py_globals['reset_sys_path']   # Modify sys.path for Jedi completion
    # Re-apply the sys.path from the shell Python
    # The system python path may not already be part of
    # the embedded Python's sys.path. This fn will check.
    insert_system_py_sitepath()
    if not msg_suppress:
        print('Conda env deactivated.')

def vim_conda_runshell(cmd):
    """ Run external shell command """
    return check_output(cmd, shell=True, executable=os.getenv('SHELL'),
                        # Needed to avoid "WindowsError: [Error 6] The handle
                        # is invalid" When launching gvim.exe from a CMD shell.
                        # (gvim from icon seems fine!?) See also:
                        # http://bugs.python.org/issue3905
                        # stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        # stderr=subprocess.PIPE)
                        stdin=PIPE, stderr=PIPE).decode('utf-8')


def vim_conda_runpyshell(cmd):
    """ Run python external python command """
    return check_output('python -c "{}"'.format(cmd), shell=True,
                        executable=os.getenv('SHELL'),
                        stdin=PIPE, stderr=PIPE).decode('utf-8')


def get_conda_info_dict():
    """ Example output:
    {
      "channels": [
        "http://repo.continuum.io/pkgs/free/osx-64/",
        "http://repo.continuum.io/pkgs/free/noarch/",
        "http://repo.continuum.io/pkgs/pro/osx-64/",
        "http://repo.continuum.io/pkgs/pro/noarch/"
      ],
      "conda_build_version": "1.1.0",
      "conda_version": "3.9.0",
      "default_prefix": "/Users/calebhattingh/anaconda",
      "envs": [
        "/Users/calebhattingh/anaconda/envs/django3",
        "/Users/calebhattingh/anaconda/envs/falcontest",
        "/Users/calebhattingh/anaconda/envs/misutesting",
        "/Users/calebhattingh/anaconda/envs/partito",
        "/Users/calebhattingh/anaconda/envs/py26",
        "/Users/calebhattingh/anaconda/envs/py27",
        "/Users/calebhattingh/anaconda/envs/py3",
        "/Users/calebhattingh/anaconda/envs/py34"
      ],
      "envs_dirs": [
        "/Users/calebhattingh/anaconda/envs"
      ],
      "is_foreign": false,
      "pkgs_dirs": [
        "/Users/calebhattingh/anaconda/pkgs"
      ],
      "platform": "osx-64",
      "python_version": "2.7.9.final.0",
      "rc_path": null,
      "requests_version": "2.5.1",
      "root_prefix": "/Users/calebhattingh/anaconda",
      "root_writable": true,
      "sys_rc_path": "/Users/calebhattingh/anaconda/.condarc",
      "user_rc_path": "/Users/calebhattingh/.condarc"
    }
    """
    output = vim_conda_runshell('conda info --json')
    return json.loads(output)


def insert_system_py_sitepath():
    """ Add the system $PATH Python's site-packages folders to the
    embedded Python's sys.path. This is for Jedi-vim code completion. """
    #import os
    cmd = "import site, sys, os; sys.stdout.write(os.path.pathsep.join(site.getsitepackages()))"
    sitedirs = vim_conda_runpyshell(cmd)
    sitedirs = sitedirs.split(os.path.pathsep)
    # The following causes errors. Jedi vim imports e.g. hashlib
    # from the stdlib, but it we've added a different stdlib to the
    # embedded sys.path, jedi loads the wrong one, causing errs.
    # Looks like we should only load site-packages.
    for sitedir in sitedirs:
        if sitedir not in sys.path:
            sys.path.insert(0, sitedir)

def setcondaplainpath():
    """ function! s:SetCondaPlainPath()

    :return: None """
    #import subprocess
    # This is quite deceiving. `os.environ` loads only a single time,
    # when the os module is first loaded. With this embedded-vim
    # Python, that means only one time. If we want to have an
    # up-to-date version of the environment, we'll have to use
    # Vim's $VAR variables and rather act on that.
    # TODO: Fix use of py getenv
    path = os.getenv('PATH')
    conda_default_env = os.getenv('CONDA_DEFAULT_ENV')
    if not conda_default_env:
        pass
    else:
        # We appear to be inside a conda env already. We want the path
        # that we would have WITHOUT being in a conda env, e.g. what
        # we'd get if `deactivate` was run.
        output = subprocess.check_output('conda info --json',
                                         shell=True,
                                         executable=os.getenv('SHELL'),
            # Needed to avoid "WindowsError: [Error 6] The handle is invalid"
            # When launching gvim.exe from a CMD shell. (gvim from icon seems
            # fine!?)
            # See also: http://bugs.python.org/issue3905
            # stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                         stdin=subprocess.PIPE,
                                         stderr=subprocess.PIPE).decode('utf-8')
        d = json.loads(output)
        # We store the path variable we get if we filter out all the paths
        # that match the current conda "default_prefix".
        # TODO Check whether the generator comprehension also works.
        path = os.pathsep.join([x for x in path.split(os.pathsep)
                                if d['default_prefix'] not in x])
    vim.command("let l:temppath = '" + path + "'")

def condaactivate():
    """ function! s:CondaActivate(envname, envpath, envsroot) """
    #import os
    #import vim
    # It turns out that `os.environ` is loaded only once. Therefore it
    # doesn't see the changes we just made above to the vim process env,
    # and so we will need to set these
    os.environ['CONDA_DEFAULT_ENV'] = vim.eval('a:envname')
    os.environ['PATH'] = vim.eval('$PATH')

def condadeactivate():
    """ function! s:CondaDeactivate() """
    #import os
    #import vim
    # It turns out that `os.environ` is loaded only once. Therefore it
    # doesn't see the changes we just made above to the vim process env,
    # and so we will need to update the embedded Python's version of
    # `os.environ` manually.
    if 'CONDA_DEFAULT_ENV' in os.environ:
        del os.environ['CONDA_DEFAULT_ENV']
    os.environ['PATH'] = vim.eval('$PATH')

def conda_startup_env():
    """ Get conda startup env

     This is happening at script startup. It looks like a conda env
     was already activated before launching vim, so we need to make
     the required changes internally.
     """
    #import vim
    #import os
    envname = vim.eval('g:conda_startup_env')
    # Need to get the root "envs" dir in order to build the
    # complete path the to env.
    d = get_conda_info_dict()
    roots = [os.path.dirname(x) for x in d['envs']
             if envname == os.path.split(x)[-1]]

    if len(roots) > 1:
        print('Found more than one matching env, '
              'this should never happen.')
    elif len(roots) == 0:
        print('\nCould not find a matching env in the list. '
              '\nThis probably means that you are using a local '
              '\n(prefix) Conda env.'
              '\n '
              '\nThis should be fine, but changing to a named env '
              '\nmay make it difficult to reactivate the prefix env.'
              '\n ')
        vim.command('let g:conda_startup_was_prefix = 1')
    else:
        root = roots[0]
        envpath = os.path.join(root, envname)
        # Reset the env paths back to root
        # (This will also modify sys.path to include the site-packages
        # folder of the Python on the system $PATH)
        conda_deactivate()
        # Re-activate.
        conda_activate(envname, envpath, root)

def conda_change_env():
    """ Obtain conda information.
    
    It's great they provide output in
    json format because it's a short trip to a dict.
    """
    #import vim
    #import os

    d = get_conda_info_dict()

    # We want to display the env names to the user, not the full paths, but
    # we need the full paths for things like $PATH modification and others.
    # Thus, we make a dict that maps env name to env path.
    # Note the juggling with decode and encode. This is being done to strip
    # the annoying `u""` unicode prefixes. There is likely a better way to
    # do this. Help would be appreciated.
    # keys = [os.path.basename(e).decode().encode('ascii') for e in d['envs']]
    #keys = [os.path.basename(e).encode('utf-8') for e in d['envs']]
    keys = [os.path.basename(e) for e in d['envs']]
    # Create the mapping {envname: envdir}
    envnames = dict(zip(keys, d['envs']))
    # Add the root as an option (so selecting `root` will trigger a deactivation
    envnames['root'] = d['root_prefix']
    # Detect the currently-selected env. Remove it from the selectable options.
    default_prefix = d['default_prefix']
    for key, value in envnames.items():
        if value == default_prefix:
            current_env = key
            break
    # Don't provide current_env as an option for user
    if current_env in envnames:
        del envnames[current_env]

    # Provide the selectable options to the `input()` callback function via
    # a global var: `g:condaenvs`
    # startup_env = vim.eval('g:conda_startup_env')
    # prefix_dir = os.path.split(startup_env)[-1]
    # prefix_name = '[prefix]' + prefix_dir
    # if vim.eval('conda_startup_was_prefix') == 1:
    #     extra=[prefix_name]
    # else:
    #     extra=[]
    vim.command('let g:condaenvs = "' + '\n'.join(envnames.keys()) + '"')
    # Ask the user to choose a new env
    choice = python_input("Change conda env [current: {}]: ".format(current_env))
    vim.command('redraw')


    if choice == 'root':
        conda_deactivate()
    elif choice in envnames:
        conda_activate(choice, envnames[choice], os.path.dirname(envnames[choice]))
    elif len(choice) > 0:
        vim.command('echo "Selected env `{}` not found."'.format(choice))
    else:
        # Do nothing, i.e. no change or message
        pass
    vim.command('redraw')
