.. contents:: **thank-you-stars** inspired by `teppeis/thank-you-stars <https://github.com/teppeis/thank-you-stars>`__
   :backlinks: top
   :depth: 2


Summary
============================================
`thank-you-stars <https://github.com/thombashi/thank-you-stars>`__ is a CLI tool to stars to a PyPI package and its dependencies hosted on GitHub.


.. image:: https://badge.fury.io/py/thank-you-stars.svg
    :target: https://badge.fury.io/py/thank-you-stars
    :alt: PyPI package version

.. image:: https://img.shields.io/pypi/pyversions/thank-you-stars.svg
    :target: https://pypi.org/project/thank-you-stars/
    :alt: Supported Python versions


Usage
============================================

Prerequisite
--------------------------------------------
- Generate a personal access token at `GitHub developer settings <https://github.com/settings/tokens>`__ with ``public_repo`` scope
- Install target PyPI packages

Basic usage
--------------------------------------------------------------------------------------

.. code-block::

    $ thank-you-stars <PyPI package>

``thank-you-stars`` will do:

1. Find a repository on GitHub correlated with the PyPI package
2. Star the repository if found
3. Repeat 1. and 2. for each of the dependency packages


Initial setup and add stars to GitHub repositories
--------------------------------------------------------------------------------------
With ``--setup`` option, you can configure an access token and then star to repositories.

.. code-block::

    $ thank-you-stars thank-you-stars --setup
    personal access token (required): <input personal access token>
    Collect package info: 100%|████████████████████████| 2/2 [00:00<00:00, 196.82it/s]
    Collect GitHub info: 100%|████████████████████████| 14/14 [00:00<00:00, 29.11it/s]
    [INFO] tys: skip owned repository: thank-you-stars
    [INFO] tys: skip owned repository: thombashi/DateTimeRange
    [INFO] tys: star to PyGithub/PyGithub
    [INFO] tys: star to tartley/colorama
    [INFO] tys: star to getlogbook/logbook
    [INFO] tys: skip owned repository: thombashi/mbstrdecoder
    [INFO] tys: skip owned repository: thombashi/msgfy
    [INFO] tys: skip owned repository: thombashi/pathvalidate
    [INFO] tys: skip owned repository: thombashi/pytablewriter
    [INFO] tys: star to requests/requests
    [INFO] tys: star to pypa/setuptools
    [INFO] tys: star to simplejson/simplejson
    [INFO] tys: skip owned repository: thombashi/subprocrunner
    [INFO] tys: star to tqdm/tqdm

Once setup is completed, ``--setup`` option not required for subsequent executions.


Add stars GitHub repositories from a package source
-----------------------------------------------------------
.. code-block::

    $ cd <path to a package source>
    $ thank-you-stars .
    [INFO] tys: star to xxxx
    ...


Check starred status
--------------------------------------------
.. code-block::

    $ thank-you-stars thank-you-stars --check
    Collect package info: 100%|███████████████████████| 2/2 [00:00<00:00, 196.82it/s]
    Collect GitHub info: 100%|███████████████████████| 14/14 [00:00<00:00, 29.11it/s]
    |     Package     |        Repository         | Starred | Owner |
    |-----------------|---------------------------|:-------:|:-----:|
    | thank-you-stars | thombashi/thank-you-stars |         |   X   |
    | DateTimeRange   | thombashi/DateTimeRange   |         |   X   |
    | PyGithub        | PyGithub/PyGithub         |    X    |       |
    | colorama        | tartley/colorama          |    X    |       |
    | logbook         | getlogbook/logbook        |    X    |       |
    | mbstrdecoder    | thombashi/mbstrdecoder    |         |   X   |
    | msgfy           | thombashi/msgfy           |         |   X   |
    | pathvalidate    | thombashi/pathvalidate    |         |   X   |
    | pytablewriter   | thombashi/pytablewriter   |         |   X   |
    | requests        | requests/requests         |    X    |       |
    | setuptools      | pypa/setuptools           |    X    |       |
    | simplejson      | simplejson/simplejson     |    X    |       |
    | subprocrunner   | thombashi/subprocrunner   |         |   X   |
    | tqdm            | tqdm/tqdm                 |    X    |       |


Increase the repository traversal depth
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block::

    $ thank-you-stars thank-you-stars --check --depth 3 -v
    Collect package info: 100%|████████████████████████| 4/4 [00:00<00:00, 185.04it/s]
    Collect GitHub info: 100%|██████████████████████| 27/27 [00:00<00:00, 1414.71it/s]
    |     Package     |        Repository         | Starred | Owner | Depth |
    |-----------------|---------------------------|:-------:|:-----:|------:|
    | thank-you-stars | thombashi/thank-you-stars |         |   X   |     0 |
    | DateTimeRange   | thombashi/DateTimeRange   |         |   X   |     1 |
    | PyGithub        | PyGithub/PyGithub         |    X    |       |     1 |
    | colorama        | tartley/colorama          |    X    |       |     1 |
    | logbook         | getlogbook/logbook        |    X    |       |     1 |
    | mbstrdecoder    | thombashi/mbstrdecoder    |         |   X   |     1 |
    | msgfy           | thombashi/msgfy           |         |   X   |     1 |
    | pathvalidate    | thombashi/pathvalidate    |         |   X   |     1 |
    | pytablewriter   | thombashi/pytablewriter   |         |   X   |     1 |
    | requests        | requests/requests         |    X    |       |     1 |
    | setuptools      | pypa/setuptools           |    X    |       |     1 |
    | simplejson      | simplejson/simplejson     |    X    |       |     1 |
    | subprocrunner   | thombashi/subprocrunner   |         |   X   |     1 |
    | tqdm            | tqdm/tqdm                 |    X    |       |     1 |
    | DataProperty    | thombashi/DataProperty    |         |   X   |     2 |
    | certifi         | certifi/python-certifi    |         |       |     2 |
    | chardet         | chardet/chardet           |    X    |       |     2 |
    | deprecated      | tantale/deprecated        |         |       |     2 |
    | dominate        | Knio/dominate             |    X    |       |     2 |
    | idna            | kjd/idna                  |         |       |     2 |
    | pyjwt           | jpadilla/pyjwt            |         |       |     2 |
    | python-dateutil | paxan/python-dateutil     |         |       |     2 |
    | six             | benjaminp/six             |    X    |       |     2 |
    | tabledata       | thombashi/tabledata       |         |   X   |     2 |
    | typepy          | thombashi/typepy          |         |   X   |     2 |
    | urllib3         | urllib3/urllib3           |         |       |     2 |
    | wrapt           | GrahamDumpleton/wrapt     |         |       |     3 |


Command help
--------------------------------------------
.. code-block::

    $ thank-you-stars -h
    usage: thank-you-stars [-h] [--version] [--token TOKEN] [--config CONFIG]
                           [--setup] [--check] [-v] [--depth DEPTH]
                           [--include-owner-repo] [--no-cache] [--dry-run]
                           [--debug | --quiet] [--stacktrace]
                           target

    Give stars a PyPI package and its dependencies.

    positional arguments:
      target                PyPI package name or path to the package source code
                            directory

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      --dry-run             Do no harm.
      --debug               for debug print.
      --quiet               suppress execution log messages.

    Configurations:
      --token TOKEN         GitHub personal access token that has public_repo
                            scope.
      --config CONFIG       path to a conig file. the config file expected to
                            contain token: { "token" : <GitHub personal access
                            token that has public_repo scope> } (defaults to
                            ~/.thank-you-stars.json).",
      --setup               setup token interactively, and then starring.

    Star Status:
      --check               list starred status for each package with tabular
                            format and exit. does not actually star to found
                            GitHub repositories.
      -v, --verbosity       increase output verbosity.

    Repository Search:
      --depth DEPTH         depth to recursively find dependencies of
                            dependencies." 0 means to star specified the package
                            only. 1 means to star specified the package and its
                            dependencies. equals to 2 or greater will increase the
                            depth of traverse that dependencies of dependencies.
      --include-owner-repo  starred to repositories that owned by you.
      --no-cache            disable the local caches.

    Debug:
      --stacktrace          print stack trace for debug information. --debug
                            option required to see the debug print.

    Issue tracker: https://github.com/thombashi/thank-you-stars/issues


Installation
============================================
::

    pip install thank-you-stars


Dependencies
============================================
Python 2.7+ or 3.5+

- `appconfigpy <https://github.com/thombashi/appconfigpy>`__
- `colorama <https://github.com/tartley/colorama>`__
- `DateTimeRange <https://github.com/thombashi/DateTimeRange>`__
- `Logbook <https://logbook.readthedocs.io/en/stable/>`__
- `mbstrdecoder <https://github.com/thombashi/mbstrdecoder>`__
- `msgfy <https://github.com/thombashi/msgfy>`__
- `pathvalidate <https://github.com/thombashi/pathvalidate>`__
- `PyGithub <https://pygithub.readthedocs.io/en/latest/>`__
- `pytablewriter <https://github.com/thombashi/pytablewriter>`__
- `retryrequests <https://github.com/thombashi/retryrequests>`__
- `simplejson <https://github.com/simplejson/simplejson>`__
- `subprocrunner <https://github.com/thombashi/subprocrunner>`__
- `tqdm <https://github.com/tqdm/tqdm>`__
