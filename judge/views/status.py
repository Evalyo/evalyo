from collections import defaultdict
from functools import partial

from django.shortcuts import render
from django.utils.translation import gettext as _
from packaging import version

from judge.models import Judge, Language, RuntimeVersion

__all__ = ["status_all", "status_table"]


def get_judges(request):
    if request.user.is_superuser or request.user.is_staff:
        return True, Judge.objects.order_by("-online", "name")
    return False, Judge.objects.filter(online=True)


def status_all(request):
    see_all, judges = get_judges(request)
    return render(
        request,
        "status/judge-status.html",
        {
            "title": _("Status"),
            "judges": judges,
            "runtime_version_data": Judge.runtime_versions(),
            "see_all_judges": see_all,
        },
    )


def status_table(request):
    see_all, judges = get_judges(request)
    return render(
        request,
        "status/judge-status-table.html",
        {
            "judges": judges,
            "runtime_version_data": Judge.runtime_versions(),
            "see_all_judges": see_all,
        },
    )


class LatestList(list):
    __slots__ = ("versions", "is_latest")


def compare_version_list(x, y):
    if sorted(x.keys()) != sorted(y.keys()):
        return False
    for k in x:
        if len(x[k]) != len(y[k]):
            return False
        for a, b in zip(x[k], y[k], strict=False):
            if a.name != b.name:
                return False
            if a.version != b.version:
                return False
    return True


def _build_initial_matrix():
    """Build initial matrix of runtime versions by judge and language."""
    matrix = defaultdict(partial(defaultdict, LatestList))
    for runtime in RuntimeVersion.objects.filter(judge__online=True).order_by("priority"):
        matrix[runtime.judge_id][runtime.language_id].append(runtime)
    return matrix


def _group_judges_by_name(matrix, judges):
    """Group judges by their base name pattern."""
    groups = defaultdict(list)
    for judge, data in matrix.items():
        name_tuple = judges[judge].rpartition(".")
        groups[name_tuple[0] or name_tuple[-1]].append((judges[judge], data))
    return groups


def _find_representative_judge(data):
    """Find the representative judge for a group of judges with similar versions."""
    ds = list(range(len(data)))
    size = [1] * len(data)

    for i, (_p, x) in enumerate(data):
        if ds[i] != i:
            continue
        for j, (_q, y) in enumerate(data):
            if i != j and compare_version_list(x, y):
                ds[j] = i
                size[i] += 1
                size[j] = 0

    return max(range(len(data)), key=size.__getitem__), ds


def _consolidate_groups(groups):
    """Consolidate grouped judges, merging similar version data."""
    matrix = {}

    for group, data in groups.items():
        if len(data) == 1:
            judge, data = data[0]
            matrix[judge] = data
            continue

        rep, ds = _find_representative_judge(data)
        matrix[group] = data[rep][1]

        for i, (j, x) in enumerate(data):
            if ds[i] != rep:
                matrix[j] = x

    return matrix


def _calculate_latest_versions(matrix):
    """Calculate the latest versions for each language across all judges."""
    latest = defaultdict(list)

    for data in matrix.values():
        for language, versions in data.items():
            versions.versions = [version.parse(runtime.version) for runtime in versions]
            if versions.versions > latest[language]:
                latest[language] = versions.versions

    return latest


def _mark_latest_versions(matrix, latest):
    """Mark which versions are the latest for each language."""
    for data in matrix.values():
        for language, versions in data.items():
            versions.is_latest = versions.versions == latest[language]


def version_matrix(request):
    """Display a matrix of runtime versions across judges and languages."""
    judges = {judge.id: judge.name for judge in Judge.objects.filter(online=True)}
    languages = Language.objects.filter(judges__online=True).distinct()

    # Build and process the version matrix
    initial_matrix = _build_initial_matrix()
    groups = _group_judges_by_name(initial_matrix, judges)
    matrix = _consolidate_groups(groups)

    # Calculate and mark latest versions
    latest = _calculate_latest_versions(matrix)
    _mark_latest_versions(matrix, latest)

    languages = sorted(languages, key=lambda lang: version.parse(lang.name))
    return render(
        request,
        "status/versions.html",
        {
            "title": _("Version"),
            "judges": sorted(matrix.keys()),
            "languages": languages,
            "matrix": matrix,
        },
    )
