import itertools
import json
from urllib.parse import quote

from jinja2.ext import Extension
from mptt.utils import get_cached_trees
from statici18n.templatetags.statici18n import inlinei18n

from judge.highlight_code import highlight_code
from judge.user_translations import gettext

from . import (
    camo,
    datetime,
    filesize,
    gravatar,
    language,
    markdown,
    rating,
    reference,
    registry,
    render,
    social,
    spaceless,
    submission,
    timedelta,
)
from . import (
    format as format_utils,
)

registry.function("str", str)
registry.jinja_filter("str", str)
registry.jinja_filter("json", json.dumps)
registry.jinja_filter("highlight", highlight_code)
registry.jinja_filter("urlquote", quote)
registry.jinja_filter("roundfloat", round)
registry.function("inlinei18n", inlinei18n)
registry.function("mptt_tree", get_cached_trees)
registry.function("user_trans", gettext)


@registry.function
def counter(start=1):
    return itertools.count(start).__next__


class DMOJExtension(Extension):
    def __init__(self, env):
        super().__init__(env)
        env.globals.update(registry.global_functions)
        env.filters.update(registry.filters)
        env.tests.update(registry.tests)
