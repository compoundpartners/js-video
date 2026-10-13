"""
Resolves external video providers (YouTube, Vimeo) from an embed link.

Detection happens here, in Python, so that templates and the facade JavaScript
receive an already resolved provider and thumbnail URL. Previous site-level
implementations guessed the provider in the browser from the length of the
video id, which misidentifies the (uncommon but real) 11 digit Vimeo ids as
YouTube ids.
"""
import re


class Provider:
    name = ''
    # Identifies the provider. Matched against the whole embed link.
    url_re = None
    # Extracts the video id. Group 1 must be the id.
    id_re = None
    # Thumbnail URL templates, most preferred first. The facade falls through
    # to the next one when a thumbnail fails to load, which YouTube's
    # ``maxresdefault`` does for any video never published above 720p.
    thumbnail_templates = ()

    def __init__(self, video_id):
        self.video_id = video_id

    def __repr__(self):
        return '<{} {}>'.format(self.name, self.video_id)

    @classmethod
    def from_link(cls, link):
        """Return an instance for ``link``, or None if it is not ours."""
        if not cls.url_re.search(link):
            return None
        match = cls.id_re.search(link)
        if match is None:
            # Our host, but no id we recognise. Report no provider rather than
            # building thumbnail URLs that are certain to 404.
            return None
        return cls(match.group(1))

    def thumbnail_urls(self):
        """Candidate thumbnail URLs, most preferred first."""
        return [
            template.format(id=self.video_id)
            for template in self.thumbnail_templates
        ]


class YouTube(Provider):
    name = 'youtube'
    url_re = re.compile(
        r'(?:^|//|\.)(?:youtube(?:-nocookie)?\.com|youtu\.be)/',
        re.IGNORECASE,
    )
    id_re = re.compile(
        r'(?:/embed/|/shorts/|/live/|/v/|youtu\.be/|[?&]v=)([A-Za-z0-9_-]{11})'
    )
    thumbnail_templates = (
        '//i.ytimg.com/vi_webp/{id}/maxresdefault.webp',
        '//i.ytimg.com/vi/{id}/hqdefault.jpg',
    )


class Vimeo(Provider):
    name = 'vimeo'
    url_re = re.compile(r'(?:^|//|\.)(?:player\.)?vimeo\.com/', re.IGNORECASE)
    id_re = re.compile(
        r'vimeo\.com/'
        r'(?:video/|channels/[\w-]+/|groups/[\w-]+/videos/)?'
        r'(\d+)',
        re.IGNORECASE,
    )
    # Vimeo has no public per-id thumbnail host of its own; vumbnail.com
    # proxies the oEmbed API. It cannot see unlisted or password protected
    # videos, so those need a poster uploading.
    thumbnail_templates = ('//vumbnail.com/{id}.jpg',)


PROVIDERS = (YouTube, Vimeo)


def get_provider(link):
    """Return a Provider instance for ``link``, or None when unrecognised."""
    if not link:
        return None
    for provider in PROVIDERS:
        resolved = provider.from_link(link)
        if resolved is not None:
            return resolved
    return None
