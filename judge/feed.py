from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.syndication.views import Feed
from django.core.cache import cache
from django.utils import timezone
from django.utils.feedgenerator import Atom1Feed

from judge.jinja2.markdown import markdown
from judge.models import BlogPost, Comment, Problem


class ProblemFeed(Feed):
    title = f"Recently Added {settings.SITE_NAME} Problems"
    link = "/"
    description = f"The latest problems added on the {settings.SITE_LONG_NAME} website"

    def items(self):
        return Problem.get_public_problems().order_by("-date", "-id")[:25]

    def item_title(self, problem):
        return problem.name

    def item_description(self, problem):
        key = f"problem_feed:{problem.id}"
        desc = cache.get(key)
        if desc is None:
            desc = str(markdown(problem.description, "problem"))[:500] + "..."
            cache.set(key, desc, 86400)
        return desc

    def item_pubdate(self, problem):
        return problem.date

    item_updateddate = item_pubdate


class AtomProblemFeed(ProblemFeed):
    feed_type = Atom1Feed
    subtitle = ProblemFeed.description


class CommentFeed(Feed):
    title = f"Latest {settings.SITE_NAME} Comments"
    link = "/"
    description = f"The latest comments on the {settings.SITE_LONG_NAME} website"

    def items(self):
        return Comment.most_recent(AnonymousUser(), 25)

    def item_title(self, comment):
        return f"{comment.author.user.username} -> {comment.page_title}"

    def item_description(self, comment):
        key = f"comment_feed:{comment.id}"
        desc = cache.get(key)
        if desc is None:
            desc = str(markdown(comment.body, "comment"))
            cache.set(key, desc, 86400)
        return desc

    def item_pubdate(self, comment):
        return comment.time

    item_updateddate = item_pubdate


class AtomCommentFeed(CommentFeed):
    feed_type = Atom1Feed
    subtitle = CommentFeed.description


class BlogFeed(Feed):
    title = f"Latest {settings.SITE_NAME} Blog Posts"
    link = "/"
    description = f"The latest blog posts from the {settings.SITE_LONG_NAME}"

    def items(self):
        return BlogPost.objects.filter(visible=True, publish_on__lte=timezone.now()).order_by("-sticky", "-publish_on")

    def item_title(self, post):
        return post.title

    def item_description(self, post):
        key = f"blog_feed:{post.id}"
        summary = cache.get(key)
        if summary is None:
            summary = str(markdown(post.summary or post.content, "blog"))
            cache.set(key, summary, 86400)
        return summary

    def item_pubdate(self, post):
        return post.publish_on

    item_updateddate = item_pubdate


class AtomBlogFeed(BlogFeed):
    feed_type = Atom1Feed
    subtitle = BlogFeed.description
