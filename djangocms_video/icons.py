"""
Play button icon parsing, with optional ``djangocms_icon`` integration.

The icon is stored in a plain ``CharField`` so that the migration is identical
on every site whether or not ``djangocms_icon`` is installed. Only the admin
widget depends on it, which follows the weak dependency pattern already used
by ``djangocms_frontend`` (see its ``contrib/tooltip/forms.py``).

The stored format is the one ``djangocms_icon``'s widget writes:
``"<iconset> <icon> <color> <size>"``, e.g. ``"fas fa-play #ffffff 48"``, with
the colour and size optional. Parsing is done here rather than by importing
``IconDict`` so that the behaviour is identical with and without the picker.
"""
import re

from django.conf import settings

# Only the widget is optional; without it the field is a plain text input.
if 'djangocms_icon' in settings.INSTALLED_APPS:
    from djangocms_icon.fields import IconFieldWidget
else:
    IconFieldWidget = None

HEX_COLOR_RE = re.compile(r'^#?(?:[0-9A-F]{3}){1,2}$', re.IGNORECASE)


def parse_icon(value):
    """
    Return ``(css_classes, inline_style)`` for a stored icon string.

    Both an iconset and an icon are required, because Font Awesome needs the
    pair and because the picker posts its iconset prefix on its own when no
    icon has been chosen. A value that does not name an icon is treated as
    unset, so the caller falls through to its next default.

    Styling mirrors ``djangocms_icon``'s own ``includes/icon.html``: the colour
    is used verbatim and the size is interpreted as pixels.
    """
    if not value:
        return '', ''

    parts = value.split(None, 3)
    if len(parts) < 2:
        return '', ''

    iconset, icon = parts[0], parts[1]
    color = size = ''
    if len(parts) > 2:
        if HEX_COLOR_RE.match(parts[2]):
            color = parts[2]
            size = parts[3] if len(parts) > 3 else ''
        else:
            size = ' '.join(parts[2:])

    styles = []
    if color:
        styles.append('color:{}'.format(color))
    if size:
        styles.append('font-size:{}px'.format(size))
    return '{} {}'.format(iconset, icon), ';'.join(styles)
