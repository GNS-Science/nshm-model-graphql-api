"""
WSGI config for nzshm_model_graphql_api project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sqlite3
import subprocess
from pathlib import Path

from django.core.wsgi import get_wsgi_application
from pkg_resources import parse_version

# We want to know the sqlite3 is good to go, and in lambda this ain't ncessarily so.
if os.getenv("DEBUG"):

    cmd = ("uname", "-a")
    print(subprocess.check_output(cmd, text=True).split("\n")[0])

    cmd = ("ldd", "--version")
    print(subprocess.check_output(cmd, text=True).split("\n")[0])

    print("sqlite3 version: %s" % sqlite3.sqlite_version)
    f = Path("_sqlite3.cpython-310-x86_64-linux-gnu.so")
    print(
        "checking for _sqlite.so with path: %s is found: %s"
        % (str(f.absolute()), f.exists())
    )

if parse_version(sqlite3.sqlite_version) < parse_version("3.37"):
    # our custom binary  is '3.44', but 3.37 also works fine
    raise RuntimeError("sqlite version %s is not supported" % sqlite3.sqlite_version)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nzshm_model_graphql_api.settings")

application = get_wsgi_application()
