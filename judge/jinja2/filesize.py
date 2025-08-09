from django.template.defaultfilters import floatformat
from django.utils.html import avoid_wrapping
from django.utils.translation import gettext_lazy as _

from . import registry


def _format_size(byte_count, formats, decimals):
    byte_count = float(byte_count)

    KB = 1 << 10
    MB = 1 << 20
    GB = 1 << 30
    TB = 1 << 40
    PB = 1 << 50

    if byte_count < KB:
        return formats[0] % floatformat(byte_count, decimals[0])
    if byte_count < MB:
        return formats[1] % floatformat(byte_count / KB, decimals[1])
    if byte_count < GB:
        return formats[2] % floatformat(byte_count / MB, decimals[2])
    if byte_count < TB:
        return formats[3] % floatformat(byte_count / GB, decimals[3])
    if byte_count < PB:
        return formats[4] % floatformat(byte_count / TB, decimals[4])
    return formats[5] % floatformat(byte_count / PB, decimals[5])


@registry.jinja_filter
def kbdetailformat(kb):
    formats = [_("%s B"), _("%s KB"), _("%s MB"), _("%s GB"), _("%s TB"), _("%s PB")]
    decimals = [0, 2, 2, 2, 2, 2]
    return avoid_wrapping(_format_size(kb * 1024, formats, decimals))


@registry.jinja_filter
def kbsimpleformat(kb):
    formats = [_("%sB"), _("%sK"), _("%sM"), _("%sG"), _("%sT"), _("%sP")]
    decimals = [0, 0, 0, 0, 0, 0]
    return _format_size(kb * 1024, formats, decimals)
