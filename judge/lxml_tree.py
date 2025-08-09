import logging

from django.utils.safestring import SafeData, mark_safe
from lxml import html
from lxml.etree import ParserError, XMLSyntaxError

logger = logging.getLogger("judge.html")


class HTMLTreeString(SafeData):
    def __init__(self, html_string):
        try:
            self._tree = html.fromstring(html_string, parser=html.HTMLParser(recover=True))
        except (XMLSyntaxError, ParserError) as e:
            if html_string and (not isinstance(e, ParserError) or e.args[0] != "Document is empty"):
                logger.exception("Failed to parse HTML string")
            self._tree = html.Element("div")

    def __getattr__(self, attr):
        try:
            return getattr(self._tree, attr)
        except AttributeError:
            return getattr(str(self), attr)

    def __setattr__(self, key, value):
        if key[0] == "_":
            super().__setattr__(key, value)
        setattr(self._tree, key, value)

    def __repr__(self):
        return f"<HTMLTreeString {str(self)!r}>"

    def __str__(self):
        return mark_safe(html.tostring(self._tree, encoding="unicode"))

    def __radd__(self, other):
        return other + str(self)

    def __add__(self, other):
        return str(self) + other

    def __getitem__(self, item):
        return str(self)[item]

    def __getstate__(self):
        return str(self)

    def __setstate__(self, state):
        self._tree = html.fromstring(state)

    @property
    def tree(self):
        return self._tree


def fromstring(html_string):
    if isinstance(html_string, HTMLTreeString):
        return html_string
    return HTMLTreeString(html_string)
