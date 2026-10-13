=========
Changelog
=========

3.2.0 (2026-10-13)
==================

Click-to-play poster overlay
----------------------------
* Embedded videos (YouTube, Vimeo) now render a poster and a play button, and
  only load the provider's iframe once the visitor clicks play. This keeps the
  provider's player payload and cookies off the initial page load.
* The ``Poster`` field moved out of "Advanced settings" and is shown by
  default; set ``DJANGOCMS_VIDEO_ENABLE_POSTER = False`` to hide it again.
* Without an uploaded poster the provider's own thumbnail is used. Disable
  with ``DJANGOCMS_VIDEO_POSTER_FALLBACK = False``.

Configurable play button
------------------------
* New ``DJANGOCMS_VIDEO_PLAY_BUTTON_IMAGE`` and
  ``DJANGOCMS_VIDEO_PLAY_BUTTON_ICON`` settings set the site-wide button.
* New per-plugin ``Play button image`` and ``Play button icon`` fields
  override it for a single video. The icon field uses the ``djangocms_icon``
  picker when that app is installed, and is a plain text input otherwise.

Other changes
-------------
* Provider detection moved from the browser into ``providers.py``. It is based
  on the host rather than the length of the video id, which misidentified
  11 digit Vimeo ids as YouTube ids.
* YouTube posters now fall back from ``maxresdefault`` to ``hqdefault``
  instead of showing a broken image for videos never published above 720p.
* The play button is a real ``<button>`` with an accessible label, and the
  iframe now carries a ``title``; both were previously missing.
* The Attributes and Parameters fields are applied to the deferred iframe.
* Embeds are forced to https. Upstream canonicalises YouTube to the protocol
  relative ``//www.youtube.com/embed/{id}``, which resolves to http on a site
  served over http and is then blocked by a scheme specific CSP ``frame-src``.
* The player is inserted before the poster is torn down, so a third party
  MutationObserver that throws cannot leave the plugin empty.
* Vimeo page URLs are rewritten to player URLs on save, as YouTube URLs
  already were. Unlisted video hashes are preserved.
* The player markup moved to ``djangocms_video/includes/video_player.html`` so
  that a site can wrap it without copying it.
* Ships ``static/djangocms_video/{css,js}`` for the facade. The template
  registers them through sekizai, which is already a django-cms dependency and
  is now declared explicitly.
* Merged upstream ``djangocms-video`` master (5 commits, no new migrations),
  picking up its pyproject packaging, ruff config and django CMS 5.1 test
  matrix. The distribution name stays ``js-video``.

3.1.0 (2022-12-07)
==================

What's Changed
--------------
* Add GitHub Actions by @crydotsnake in https://github.com/django-cms/djangocms-video/pull/61
* Add requirement files by @crydotsnake in https://github.com/django-cms/djangocms-video/pull/62
* Plugin code block must be identifiable by CSS by @macolo in https://github.com/django-cms/djangocms-video/pull/64
* Create PR template by @Kaushal-Dhungel in https://github.com/django-cms/djangocms-video/pull/65
* FEATURE: adjust setup metadata by @crydotsnake in https://github.com/django-cms/djangocms-video/pull/67
* feat: Add migrations for Django 4.2 by @mogoh in https://github.com/django-cms/djangocms-video/pull/73

New Contributors
----------------
* @crydotsnake made their first contribution in https://github.com/django-cms/djangocms-video/pull/61
* @macolo made their first contribution in https://github.com/django-cms/djangocms-video/pull/64
* @Kaushal-Dhungel made their first contribution in https://github.com/django-cms/djangocms-video/pull/65
* @mogoh made their first contribution in https://github.com/django-cms/djangocms-video/pull/73

**Full Changelog**: https://github.com/django-cms/djangocms-video/compare/3.0.0...3.1.0

3.0.0 (2020-09-02)
==================

* Added support for Django 3.1
* Dropped support for Python 2.7 and Python 3.4
* Dropped support for Django < 2.2
* Added setting DJANGOCMS_VIDEO_YOUTUBE_EMBED_URL to allow overriding the
  default canonical YouTube URL


2.3.0 (2020-01-29)
==================

* Added support for Django 3.0
* Added further tests to raise coverage
* Fixed smaller issues found during testing


2.2.0 (2019-05-22)
==================

* Added support for Django 2.2 and django CMS 3.7
* Removed support for Django 2.0
* Extended test matrix
* Added isort and adapted imports
* Adapted code base to align with other supported addons


2.1.1 (2018-12-07)
==================

* Fixed test matrix
* Exclude tests folder from release build (#46)


2.1.0 (2018-11-13)
==================

* Removed support for Django 1.8, 1.9, 1.10


2.0.5 (2018-10-19)
==================

* Deal with missing context from aldryn-search
* Add support for newer Django versions
* Add parameters for embed_link
* Fix swappable filer image model support


2.0.4 (2017-08-15)
==================

* Added URL parsing for the embed url. It now accepts various versions of YouTube urls and converts them to an embed link.
* Added the python3.5 test env


2.0.3 (2016-11-22)
==================

* Prevent changes to ``DJANGOCMS_VIDEO_XXX`` settings from requiring new
  migrations
* Changed naming of ``Aldryn`` to ``Divio Cloud``
* Adapted testing infrastructure (tox/travis) to incorporate
  django CMS 3.4 and dropped 3.2
* Updated translations


2.0.2 (2016-20-09)
==================

* Fixed an issues with migrations where Null values caused ``IntegrityError``


2.0.1 (2016-08-09)
==================
* Removed ``base.html`` for performance reasons
* Fixed faulty settings parsing in aldryn_config.py
* Fixed an issue where ValidationError wasn't imported
* Adapted private ``get_template`` method
* Updated translations


2.0.0 (2016-29-08)
==================

* Dropped flash support
* Dropped django CMS <3.3.1 support
* Dropped Django <1.8 support
* Renamed Video to VideoPlayer
* Added Video Source Plugin
* Added Video Track Plugin
* Adapted files to resemble best practices
* Updated translations


1.1.0 (2016-25-08)
==================

* Adapted README
* Added several config files for codecov, editorconfig and more
* Added a simple test case
* Added missing ``swfobject.min.js``
* Added missing ``player.swf``
* Added missing ``expressInstall.swf``
* Added missing ``get_flash_player-gif``
* Fixed template to include missing files


1.0.0 (2016-03-04)
==================

* Public release
