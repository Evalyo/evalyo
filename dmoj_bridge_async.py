import os

import gevent.monkey  # noqa: I001, gevent must be imported here

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dmoj.settings")
gevent.monkey.patch_all()

# noinspection PyUnresolvedReferences
import django  # noqa: E402, F401, I001, I002, django must be imported here

import dmoj_install_pymysql  # noqa: E402, F401, I001, I002, imported for side effect

django.setup()

from judge.bridge.daemon import judge_daemon  # noqa: E402, I001, I002, django code must be imported here

if __name__ == "__main__":
    judge_daemon()
