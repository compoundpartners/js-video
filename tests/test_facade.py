"""Tests for the click-to-play facade: provider resolution, poster and button."""
from django.test import TestCase, override_settings

from djangocms_video import providers
from djangocms_video.models import VideoPlayer


class ProviderResolutionTestCase(TestCase):

    def test_youtube_url_forms(self):
        for link in [
            '//www.youtube.com/embed/dQw4w9WgXcQ',
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://youtu.be/dQw4w9WgXcQ',
            'https://www.youtube.com/shorts/dQw4w9WgXcQ',
            'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ',
        ]:
            with self.subTest(link=link):
                provider = providers.get_provider(link)
                self.assertIsNotNone(provider)
                self.assertEqual(provider.name, 'youtube')
                self.assertEqual(provider.video_id, 'dQw4w9WgXcQ')

    def test_vimeo_url_forms(self):
        for link in [
            '//player.vimeo.com/video/123456789',
            'https://vimeo.com/123456789',
            'https://vimeo.com/channels/staffpicks/123456789',
        ]:
            with self.subTest(link=link):
                provider = providers.get_provider(link)
                self.assertIsNotNone(provider)
                self.assertEqual(provider.name, 'vimeo')
                self.assertEqual(provider.video_id, '123456789')

    def test_eleven_digit_vimeo_id_is_not_youtube(self):
        """
        Detection is by host. An earlier implementation treated any 11
        character id as YouTube, which misidentified 11 digit Vimeo ids.
        """
        provider = providers.get_provider('//player.vimeo.com/video/12345678901')
        self.assertEqual(provider.name, 'vimeo')

    def test_unknown_provider(self):
        self.assertIsNone(providers.get_provider('https://example.com/clip.mp4'))
        self.assertIsNone(providers.get_provider(''))

    def test_known_host_without_an_id(self):
        """No id means no thumbnail URLs rather than URLs certain to 404."""
        self.assertIsNone(providers.get_provider('https://www.youtube.com/'))

    def test_youtube_thumbnails_fall_back_from_maxres(self):
        urls = providers.get_provider('https://youtu.be/dQw4w9WgXcQ').thumbnail_urls()
        self.assertEqual(len(urls), 2)
        self.assertIn('maxresdefault', urls[0])
        self.assertIn('hqdefault', urls[1])


class PosterTestCase(TestCase):

    def test_provider_thumbnail_used_without_a_poster(self):
        plugin = VideoPlayer(embed_link='//www.youtube.com/embed/dQw4w9WgXcQ')
        self.assertIn('maxresdefault', plugin.poster_url)
        self.assertEqual(len(plugin.poster_fallback_urls), 1)

    @override_settings(DJANGOCMS_VIDEO_POSTER_FALLBACK=False)
    def test_provider_thumbnail_can_be_disabled(self):
        plugin = VideoPlayer(embed_link='//www.youtube.com/embed/dQw4w9WgXcQ')
        self.assertEqual(plugin.poster_url, '')
        self.assertEqual(plugin.poster_fallback_urls, [])

    def test_no_poster_for_uploaded_sources(self):
        self.assertEqual(VideoPlayer(embed_link='').poster_url, '')

    def test_autoplay_is_added_and_parameters_kept(self):
        plugin = VideoPlayer(
            embed_link='//www.youtube.com/embed/dQw4w9WgXcQ',
            parameters={'start': '30'},
        )
        link = plugin.autoplay_embed_link
        self.assertIn('autoplay=1', link)
        self.assertIn('start=30', link)

    def test_embeds_are_forced_to_https(self):
        """
        A protocol relative link resolves to http on a site served over http,
        and a scheme specific CSP frame-src then blocks the frame.
        """
        plugin = VideoPlayer(embed_link='//www.youtube.com/embed/dQw4w9WgXcQ')
        self.assertTrue(plugin.secure_embed_link.startswith('https://'))
        self.assertTrue(plugin.autoplay_embed_link.startswith('https://'))

        plugin = VideoPlayer(embed_link='http://player.vimeo.com/video/123')
        self.assertEqual(
            plugin.secure_embed_link, 'https://player.vimeo.com/video/123',
        )

        plugin = VideoPlayer(embed_link='https://player.vimeo.com/video/123')
        self.assertEqual(
            plugin.secure_embed_link, 'https://player.vimeo.com/video/123',
        )

    def test_iframe_title_falls_back_to_a_generic_name(self):
        self.assertEqual(
            VideoPlayer(embed_link='//www.youtube.com/embed/dQw4w9WgXcQ').iframe_title,
            'Video',
        )
        self.assertEqual(
            VideoPlayer(embed_link='x', label='Our story').iframe_title,
            'Our story',
        )


@override_settings(DJANGOCMS_VIDEO_PLAY_BUTTON_IMAGE='', DJANGOCMS_VIDEO_PLAY_BUTTON_ICON='')
class PlayButtonTestCase(TestCase):
    """Precedence: plugin image, plugin icon, site image, site icon."""

    def test_nothing_configured_leaves_the_css_default(self):
        plugin = VideoPlayer()
        self.assertEqual(plugin.play_button_image_url, '')
        self.assertEqual(plugin.play_button_icon_class, '')

    @override_settings(DJANGOCMS_VIDEO_PLAY_BUTTON_ICON='fas fa-play #ffffff 48')
    def test_site_icon(self):
        plugin = VideoPlayer()
        self.assertEqual(plugin.play_button_icon_class, 'fas fa-play')
        self.assertEqual(plugin.play_button_icon_style, 'color:#ffffff;font-size:48px')

    @override_settings(DJANGOCMS_VIDEO_PLAY_BUTTON_IMAGE='img/play.png', STATIC_URL='/static/')
    def test_site_image_is_resolved_through_staticfiles(self):
        self.assertEqual(VideoPlayer().play_button_image_url, '/static/img/play.png')

    @override_settings(DJANGOCMS_VIDEO_PLAY_BUTTON_IMAGE='/media/custom/play.png')
    def test_site_image_accepts_a_ready_made_url(self):
        self.assertEqual(VideoPlayer().play_button_image_url, '/media/custom/play.png')

    @override_settings(DJANGOCMS_VIDEO_PLAY_BUTTON_IMAGE='img/play.png')
    def test_plugin_icon_beats_site_image(self):
        plugin = VideoPlayer(play_button_icon='fas fa-circle-play')
        self.assertEqual(plugin.play_button_image_url, '')
        self.assertEqual(plugin.play_button_icon_class, 'fas fa-circle-play')

    @override_settings(DJANGOCMS_VIDEO_PLAY_BUTTON_IMAGE='img/play.png', STATIC_URL='/static/')
    def test_empty_picker_value_falls_back_to_the_site_default(self):
        """The icon widget posts its iconset prefix even with no icon chosen."""
        plugin = VideoPlayer(play_button_icon='far  ')
        self.assertEqual(plugin.play_button_image_url, '/static/img/play.png')
        self.assertEqual(plugin.play_button_icon_class, '')
