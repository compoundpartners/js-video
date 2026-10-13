"""
Enables the user to add a "Video player" plugin that can render content
from external resources through an embed link or upload single files as
sources to be displayed in an HTML5 player.
"""
import json
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from cms.models import CMSPlugin
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from djangocms_attributes_field.fields import AttributesField
from filer.fields.file import FilerFileField
from filer.fields.image import FilerImageField

from . import icons, providers


# The mp4 file format is supported by all major browsers
def get_extensions():
    extensions = getattr(
        settings,
        'DJANGOCMS_VIDEO_ALLOWED_EXTENSIONS',
        ['mp4', 'webm', 'ogv'],
    )
    return extensions


# Add additional choices through the ``settings.py``.
def get_templates():
    return [
        ('default', _('Default')),
    ] + getattr(
        settings,
        'DJANGOCMS_VIDEO_TEMPLATES',
        [],
    )


class VideoPlayer(CMSPlugin):
    """
    Renders either an Iframe when ``link`` is provided or the HTML5 <video> tag
    """
    template = models.CharField(
        verbose_name=_('Template'),
        choices=get_templates(),
        default=get_templates()[0][0],
        max_length=255,
    )
    label = models.CharField(
        verbose_name=_('Label'),
        blank=True,
        max_length=255,
    )
    embed_link = models.CharField(
        verbose_name=_('Embed link'),
        blank=True,
        max_length=255,
        help_text=_(
            'Use this field to embed videos from external services '
            'such as YouTube, Vimeo or others. Leave it blank to upload video '
            'files by adding nested "Source" plugins.'
        ),
    )
    parameters = AttributesField(
        verbose_name=_('Parameters'),
        blank=True,
        help_text=_(
            'Parameters are appended to the video link if provided.'
        ),
    )
    poster = FilerImageField(
        verbose_name=_('Poster'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text=_(
            'Shown over the video until the visitor clicks play. Leave blank '
            'to use the thumbnail published by YouTube or Vimeo.'
        ),
    )
    play_button_image = FilerImageField(
        verbose_name=_('Play button image'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text=_(
            'Overrides the site-wide play button for this video. Takes '
            'precedence over the play button icon.'
        ),
    )
    play_button_icon = models.CharField(
        verbose_name=_('Play button icon'),
        blank=True,
        max_length=255,
        help_text=_(
            'Overrides the site-wide play button for this video, unless a '
            'play button image is set above.'
        ),
    )
    attributes = AttributesField(
        verbose_name=_('Attributes'),
        blank=True,
    )
    description = models.TextField(
        verbose_name=_('Description'),
        blank=True,
        null=True,
    )
    duration = models.TimeField(
        verbose_name=_('Duration'),
        blank=True,
        null=True,
    )
    upload_date = models.DateField(
        verbose_name=_('Upload Date'),
        blank=True,
        null=True,
    )
    # Add an app namespace to related_name to avoid field name clashes
    # with any other plugins that have a field with the same name as the
    # lowercase of the class name of this model.
    # https://github.com/divio/django-cms/issues/5030
    cmsplugin_ptr = models.OneToOneField(
        CMSPlugin,
        related_name='%(app_label)s_%(class)s',
        parent_link=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.label or self.embed_link or str(self.pk)

    def copy_relations(self, oldinstance):
        # Because we have a ForeignKey, it's required to copy over
        # the reference from the instance to the new plugin.
        self.poster = oldinstance.poster
        self.play_button_image = oldinstance.play_button_image

    @property
    def embed_link_with_parameters(self):
        if not self.embed_link:
            return ''
        if not self.parameters:
            return self.embed_link
        return self._append_url_parameters(self.embed_link, self.parameters)

    def _append_url_parameters(self, url, params):
        url_parts = list(urlparse(url))
        query = dict(parse_qsl(url_parts[4]))
        query.update(params)
        url_parts[4] = urlencode(query)
        return urlunparse(url_parts)

    @staticmethod
    def _force_https(url):
        """
        Serve the embed over https whatever scheme the page itself uses.

        Upstream canonicalises YouTube to the protocol relative
        ``//www.youtube.com/embed/{id}``, which resolves to http on a site
        served over http. CSP ``frame-src`` sources are scheme specific, so an
        allowlist entry of ``https://www.youtube.com`` does not match that and
        the browser blocks the frame. It only bites in local development,
        which is exactly why it is worth pinning here.
        """
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('http://'):
            return 'https://' + url[len('http://'):]
        return url

    @property
    def secure_embed_link(self):
        """``embed_link_with_parameters``, forced to https."""
        if not self.embed_link:
            return ''
        return self._force_https(self.embed_link_with_parameters)

    @property
    def autoplay_embed_link(self):
        """
        The iframe source used once the visitor clicks play.

        Built on top of ``embed_link_with_parameters`` so that anything the
        editor put in the Parameters field is kept. Both YouTube and Vimeo
        spell the flag ``autoplay=1``.
        """
        if not self.embed_link:
            return ''
        return self._append_url_parameters(
            self.secure_embed_link, {'autoplay': '1'},
        )

    @property
    def iframe_title(self):
        """
        Accessible name for the player. An untitled iframe fails WCAG, and the
        embed URL is no use to a screen reader, so fall back to a generic name.
        """
        return self.label or gettext('Video')

    @property
    def play_button_label(self):
        """Accessible name for the overlay button."""
        if self.label:
            return gettext('Play video: {label}').format(label=self.label)
        return gettext('Play video')

    @property
    def attributes_json(self):
        """
        Editor attributes, for the iframe the facade builds on click.

        Upstream applies the Attributes field to the server rendered iframe.
        The facade creates its iframe in the browser instead, so the
        attributes travel with it as JSON.
        """
        return json.dumps(self.attributes or {})

    @property
    def video_provider(self):
        """The resolved external provider, or None for uploaded sources."""
        return providers.get_provider(self.embed_link)

    @property
    def poster_urls(self):
        """
        Overlay image candidates, most preferred first.

        An uploaded poster always wins. Without one we fall back to the
        provider's own thumbnail, unless that is switched off site-wide.
        """
        if self.poster_id:
            return [self.poster.url]
        if not getattr(settings, 'DJANGOCMS_VIDEO_POSTER_FALLBACK', True):
            return []
        provider = self.video_provider
        return provider.thumbnail_urls() if provider else []

    @property
    def poster_url(self):
        urls = self.poster_urls
        return urls[0] if urls else ''

    @property
    def poster_fallback_urls(self):
        """Remaining candidates, tried by the facade when one fails to load."""
        return self.poster_urls[1:]

    @property
    def poster_alt(self):
        # The poster is decorative when it sits behind a labelled play button,
        # so an empty alt is correct unless filer has real alt text for it.
        if self.poster_id:
            return self.poster.default_alt_text or ''
        return ''

    @staticmethod
    def _static_url(path):
        """Allow settings to give either a static path or a ready-made URL."""
        if path.startswith('/') or '://' in path:
            return path
        return static(path)

    @property
    def _play_button(self):
        """
        Resolve the play button overlay.

        Returns ``(image_url, icon_class, icon_style)`` with at most one of the
        image or the icon populated. Precedence runs most specific first: this
        plugin's image, this plugin's icon, the site-wide image, the site-wide
        icon. With nothing configured all three are empty and the stylesheet
        draws its own default button.
        """
        if self.play_button_image_id:
            return self.play_button_image.url, '', ''

        classes, style = icons.parse_icon(self.play_button_icon)
        if classes:
            return '', classes, style

        default_image = getattr(
            settings, 'DJANGOCMS_VIDEO_PLAY_BUTTON_IMAGE', '',
        )
        if default_image:
            return self._static_url(default_image), '', ''

        classes, style = icons.parse_icon(
            getattr(settings, 'DJANGOCMS_VIDEO_PLAY_BUTTON_ICON', ''),
        )
        return '', classes, style

    @property
    def play_button_image_url(self):
        return self._play_button[0]

    @property
    def play_button_icon_class(self):
        return self._play_button[1]

    @property
    def play_button_icon_style(self):
        return self._play_button[2]


class VideoSource(CMSPlugin):
    """
    Renders the HTML <source> element inside of <video>.
    """
    source_file = FilerFileField(
        verbose_name=_('Source'),
        blank=False,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    text_title = models.CharField(
        verbose_name=_('Title'),
        blank=True,
        max_length=255,
    )
    text_description = models.TextField(
        verbose_name=_('Description'),
        blank=True,
    )
    attributes = AttributesField(
        verbose_name=_('Attributes'),
        blank=True,
    )

    def __str__(self):
        if self.source_file_id and self.source_file.label:
            return self.source_file.label
        return str(self.pk)

    def clean(self):
        if self.source_file and self.source_file.extension not in get_extensions():
            raise ValidationError(
                gettext('Incorrect file type: {extension}.')
                .format(extension=self.source_file.extension)
            )

    def get_short_description(self):
        if self.source_file_id and self.source_file.label:
            return self.source_file.label
        return gettext('<file is missing>')

    def copy_relations(self, oldinstance):
        # Because we have a ForeignKey, it's required to copy over
        # the reference from the instance to the new plugin.
        self.source_file = oldinstance.source_file


class VideoTrack(CMSPlugin):
    """
    Renders the HTML <track> element inside <video>.
    """
    KIND_CHOICES = [
        ('subtitles', _('Subtitles')),
        ('captions', _('Captions')),
        ('descriptions', _('Descriptions')),
        ('chapters', _('Chapters')),
    ]

    kind = models.CharField(
        verbose_name=_('Kind'),
        choices=KIND_CHOICES,
        max_length=255,
    )
    src = FilerFileField(
        verbose_name=_('Source file'),
        blank=False,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    srclang = models.CharField(
        verbose_name=_('Source language'),
        blank=True,
        max_length=255,
        help_text=_('Examples: "en" or "de" etc.'),
    )
    label = models.CharField(
        verbose_name=_('Label'),
        blank=True,
        max_length=255,
    )
    attributes = AttributesField(
        verbose_name=_('Attributes'),
        blank=True,
    )

    def __str__(self):
        label = self.kind
        if self.srclang:
            label += ' ({})'.format(self.srclang)
        return label
