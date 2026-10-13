import re

from django import forms
from django.conf import settings

from . import icons, models

YOUTUBE_URL_RE = re.compile(r'(?:(?:http://|https://|//)?(?:www\.)?youtu\.?be.*).*')
# https://stackoverflow.com/a/9102270
YOUTUBE_VIDEO_ID_RE = re.compile(r'(?:[?&]v=|/embed/|/1/|/v/|https?://(?:www\.)?youtu\.be/)([^&\n?#]+)')
DEFAULT_YOUTUBE_EMBED_URL = '//www.youtube.com/embed/{}'

VIMEO_URL_RE = re.compile(
    r'^(?:(?:https?:)?//)?(?:www\.)?vimeo\.com/', re.IGNORECASE,
)
# vimeo.com/123456789, /channels/<name>/123456789, /123456789/<unlisted hash>
VIMEO_VIDEO_ID_RE = re.compile(
    r'vimeo\.com/'
    r'(?:channels/[\w-]+/|groups/[\w-]+/videos/)?'
    r'(\d+)'
    r'(?:/(\w+))?',
    re.IGNORECASE,
)
DEFAULT_VIMEO_EMBED_URL = '//player.vimeo.com/video/{}'

# Only present when djangocms_icon is installed; see ``icons``.
ICON_WIDGETS = (
    {'play_button_icon': icons.IconFieldWidget}
    if icons.IconFieldWidget is not None
    else {}
)


class VideoPlayerPluginForm(forms.ModelForm):
    class Meta:
        model = models.VideoPlayer
        exclude = []
        widgets = ICON_WIDGETS

    def clean_embed_link(self):
        link = self.cleaned_data['embed_link']
        # let's check if it's a youtube url
        # (the low cost version)
        if YOUTUBE_URL_RE.match(link):
            # try to get the video id
            results = YOUTUBE_VIDEO_ID_RE.findall(link)
            if results:
                embed_url = getattr(settings, "DJANGOCMS_VIDEO_YOUTUBE_EMBED_URL", DEFAULT_YOUTUBE_EMBED_URL)
                link = embed_url.format(results[0])
        elif VIMEO_URL_RE.match(link):
            # Editors paste the page URL far more often than the player URL,
            # and the page URL will not render in an iframe.
            match = VIMEO_VIDEO_ID_RE.search(link)
            if match:
                embed_url = getattr(settings, "DJANGOCMS_VIDEO_VIMEO_EMBED_URL", DEFAULT_VIMEO_EMBED_URL)
                link = embed_url.format(match.group(1))
                if match.group(2):
                    # Unlisted videos only play when the hash is passed on.
                    link = '{}?h={}'.format(link, match.group(2))
        return link
