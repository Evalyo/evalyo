import errno
import os

from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .caching import finished_submission
from .models import (
    EFFECTIVE_MATH_ENGINES,
    BlogPost,
    Comment,
    Contest,
    ContestProblem,
    ContestSubmission,
    Judge,
    Language,
    License,
    MiscConfig,
    Organization,
    Problem,
    Profile,
    Submission,
    WebAuthnCredential,
)


def get_pdf_path(basename: str) -> str | None:
    if not settings.DMOJ_PDF_PROBLEM_CACHE:
        return None

    return os.path.join(settings.DMOJ_PDF_PROBLEM_CACHE, basename)


def unlink_if_exists(file):
    try:
        os.unlink(file)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


@receiver(post_save, sender=Problem)
def problem_update(sender, instance, **kwargs):
    if hasattr(instance, "_updating_stats_only"):
        return

    cache.delete_many(
        [
            make_template_fragment_key("submission_problem", (instance.id,)),
            make_template_fragment_key("problem_feed", (instance.id,)),
            f"problem_tls:{instance.id}",
            f"problem_mls:{instance.id}",
        ]
    )
    cache.delete_many(
        [
            make_template_fragment_key("problem_html", (instance.id, engine, lang))
            for lang, _ in settings.LANGUAGES
            for engine in EFFECTIVE_MATH_ENGINES
        ]
    )
    cache.delete_many(
        [make_template_fragment_key("problem_authors", (instance.id, lang)) for lang, _ in settings.LANGUAGES]
    )
    cache.delete_many([f"generated-meta-problem:{lang}:{instance.id}" for lang, _ in settings.LANGUAGES])

    for lang, _ in settings.LANGUAGES:
        cached_pdf_filename = get_pdf_path(f"{instance.code}.{lang}.pdf")
        if cached_pdf_filename is not None:
            unlink_if_exists(cached_pdf_filename)


@receiver(post_save, sender=Profile)
def profile_update(sender, instance, **kwargs):
    if hasattr(instance, "_updating_stats_only"):
        return

    cache.delete_many(
        [make_template_fragment_key("user_about", (instance.id, engine)) for engine in EFFECTIVE_MATH_ENGINES]
        + [
            make_template_fragment_key("org_member_count", (org_id,))
            for org_id in instance.organizations.values_list("id", flat=True)
        ]
    )


@receiver(post_delete, sender=WebAuthnCredential)
def webauthn_delete(sender, instance, **kwargs):
    profile = instance.user
    if profile.webauthn_credentials.count() == 0:
        profile.is_webauthn_enabled = False
        profile.save(update_fields=["is_webauthn_enabled"])


@receiver(post_save, sender=Contest)
def contest_update(sender, instance, **kwargs):
    if hasattr(instance, "_updating_stats_only"):
        return

    cache.delete_many(
        [f"generated-meta-contest:{instance.id}"]
        + [make_template_fragment_key("contest_html", (instance.id, engine)) for engine in EFFECTIVE_MATH_ENGINES]
    )


@receiver(post_delete, sender=ContestProblem)
def contest_problem_delete(sender, instance, **kwargs):
    # `contest_object` is the `Contest` object indirectly associated with the `Submission` object
    # `contest` is the `ContestSubmission` object associated with the `Submission` object
    Submission.objects.filter(contest_object=instance.contest, contest__isnull=True).update(contest_object=None)


@receiver(post_save, sender=License)
def license_update(sender, instance, **kwargs):
    cache.delete(make_template_fragment_key("license_html", (instance.id,)))


@receiver(post_save, sender=Language)
def language_update(sender, instance, **kwargs):
    cache.delete_many([make_template_fragment_key("language_html", (instance.id,)), "lang:cn_map"])


@receiver(post_save, sender=Judge)
def judge_update(sender, instance, **kwargs):
    cache.delete(make_template_fragment_key("judge_html", (instance.id,)))


@receiver(post_save, sender=Comment)
def comment_update(sender, instance, **kwargs):
    cache.delete(f"comment_feed:{instance.id}")


@receiver(post_save, sender=BlogPost)
def post_update(sender, instance, **kwargs):
    cache.delete_many(
        [
            make_template_fragment_key("post_summary", (instance.id,)),
            f"blog_slug:{instance.id}",
            f"blog_feed:{instance.id}",
        ]
    )
    cache.delete_many(
        [make_template_fragment_key("post_content", (instance.id, engine)) for engine in EFFECTIVE_MATH_ENGINES]
    )


@receiver(post_delete, sender=Submission)
def submission_delete(sender, instance, **kwargs):
    finished_submission(instance)
    instance.user._updating_stats_only = True
    instance.user.calculate_points()
    instance.problem._updating_stats_only = True
    instance.problem.update_stats()


@receiver(post_delete, sender=ContestSubmission)
def contest_submission_delete(sender, instance, **kwargs):
    participation = instance.participation
    participation.recompute_results()
    Submission.objects.filter(id=instance.submission_id).update(contest_object=None)


@receiver(post_save, sender=Organization)
def organization_update(sender, instance, **kwargs):
    cache.delete_many(
        [make_template_fragment_key("organization_html", (instance.id, engine)) for engine in EFFECTIVE_MATH_ENGINES]
    )


@receiver(post_save, sender=MiscConfig)
def misc_config_update(sender, instance, **kwargs):
    cache.delete("misc_config")


@receiver(post_delete, sender=MiscConfig)
def misc_config_delete(sender, instance, **kwargs):
    cache.delete("misc_config")


@receiver(post_save, sender=ContestSubmission)
def contest_submission_update(sender, instance, **kwargs):
    Submission.objects.filter(id=instance.submission_id).update(contest_object_id=instance.participation.contest_id)
