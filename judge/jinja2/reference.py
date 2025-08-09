import re
from collections import defaultdict
from urllib.parse import urljoin

from ansi2html import Ansi2HTMLConverter
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from lxml.html import Element

from judge import lxml_tree
from judge.models import Contest, Problem, Profile
from judge.ratings import rating_class, rating_progress

from . import registry

rereference = re.compile(r"\[(r?user):(\w+)\]")


def get_user(username, data):
    if not data:
        element = Element("span", {"class": "deleted-user"})
        element.text = username
        return element

    element = Element("span", {"class": Profile.get_user_css_class(*data)})
    link = Element("a", {"href": reverse("user_page", args=[username])})
    link.text = username
    element.append(link)
    return element


def get_user_rating(username, data):
    if not data:
        element = Element("span")
        element.text = username
        return element

    rating = data[1]
    element = Element("a", {"class": "rate-group", "href": reverse("user_page", args=[username])})
    if rating:
        rating_css = rating_class(rating)
        rate_box = Element("span", {"class": "rate-box " + rating_css})
        rate_box.append(Element("span", {"style": f"height: {rating_progress(rating):3.0f}em"}))
        user = Element("span", {"class": "rating " + rating_css})
        user.text = username
        element.append(rate_box)
        element.append(user)
    else:
        element.text = username
    return element


def get_user_info(usernames):
    return {
        name: (rank, rating)
        for name, rank, rating in Profile.objects.filter(user__username__in=usernames).values_list(
            "user__username", "display_rank", "rating"
        )
    }


reference_map = {
    "user": (get_user, get_user_info),
    "ruser": (get_user_rating, get_user_info),
}


def process_reference(text):
    # text/tail -> text/tail + elements
    last = 0
    tail = text
    prev = None
    elements = []
    for piece in rereference.finditer(text):
        if prev is None:
            tail = text[last : piece.start()]
        else:
            prev.append(text[last : piece.start()])
        prev = list(piece.groups())
        elements.append(prev)
        last = piece.end()
    if prev is not None:
        prev.append(text[last:])
    return tail, elements


def populate_list(queries, target_list, element, tail, children):
    if children:
        for elem in children:
            queries[elem[0]].append(elem[1])
        target_list.append((element, tail, children))


def update_tree(target_list, results, is_tail=False):
    for element, text, children in target_list:
        after = []
        for ref_type, name, tail in children:
            child = reference_map[ref_type][0](name, results[ref_type].get(name))
            child.tail = tail
            after.append(child)

        after = iter(reversed(after))
        if is_tail:
            element.tail = text
            link = element.getnext()
            if link is None:
                link = next(after)
                element.getparent().append(link)
        else:
            element.text = text
            link = next(after)
            element.insert(0, link)
        for child in after:
            link.addprevious(child)
            link = child


@registry.jinja_filter
def reference(text):
    tree = lxml_tree.fromstring(text)
    texts = []
    tails = []
    queries = defaultdict(list)
    for element in tree.iter():
        if element.text:
            populate_list(queries, texts, element, *process_reference(element.text))
        if element.tail:
            populate_list(queries, tails, element, *process_reference(element.tail))

    results = {ref_type: reference_map[ref_type][1](values) for ref_type, values in queries.items()}
    update_tree(texts, results, is_tail=False)
    update_tree(tails, results, is_tail=True)
    return tree


@registry.jinja_filter
def item_title(item):
    if isinstance(item, Problem | Contest):
        return item.name
    return "<Unknown>"


@registry.function
def link_user(user):
    if isinstance(user, Profile):
        user, profile = user.user, user
    elif isinstance(user, AbstractUser):
        profile = user.profile
    elif type(user).__name__ == "ContestRankingProfile":
        user, profile = user.user, user
    else:
        raise ValueError(f"Expected profile or user, got {type(user)}")
    return mark_safe(
        f'<span class="{profile.css_class}">'
        f'<a href="{escape(reverse("user_page", args=[user.username]))}">'
        f"{escape(profile.display_name)}</a></span>"
    )


@registry.function
@registry.render_with("user/link-list.html")
def link_users(users):
    return {"users": users}


@registry.function
@registry.render_with("runtime-version-fragment.html")
def runtime_versions(versions):
    return {"runtime_versions": versions}


@registry.jinja_filter(name="absolutify")
def absolute_links(text, url):
    tree = lxml_tree.fromstring(text)
    for anchor in tree.xpath(".//a"):
        href = anchor.get("href")
        if href:
            anchor.set("href", urljoin(url, href))
    return tree


@registry.function(name="urljoin")
def join(first, second, *rest):
    if not rest:
        return urljoin(first, second)
    return urljoin(urljoin(first, second), *rest)


@registry.jinja_filter(name="ansi2html")
def ansi2html(s):
    return mark_safe(Ansi2HTMLConverter(inline=True).convert(s, full=False))
