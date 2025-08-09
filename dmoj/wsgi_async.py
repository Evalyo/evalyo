import os

import gevent.monkey  # noqa: I001, gevent must be imported here

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dmoj.settings")
gevent.monkey.patch_all()

# noinspection PyUnresolvedReferences
from django.core.wsgi import get_wsgi_application  # noqa: E402, I001, I002, django must be imported here

import dmoj_install_pymysql  # noqa: E402, F401, I001, I002, imported for side effect

application = get_wsgi_application()
