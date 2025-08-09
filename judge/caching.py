from django.core.cache import cache


def finished_submission(sub):
    keys = [f"user_complete:{sub.user_id}", f"user_attempted:{sub.user_id}"]
    if hasattr(sub, "contest"):
        participation = sub.contest.participation
        keys += [f"contest_complete:{participation.id}"]
        keys += [f"contest_attempted:{participation.id}"]
    cache.delete_many(keys)
