/*
 * Click-to-play facade for embedded videos.
 *
 * The server renders a poster and a play button; the provider's iframe is only
 * created once the visitor activates the button. Keeping the iframe out of the
 * initial page load avoids downloading the provider's player and avoids
 * setting its cookies before the visitor has asked for the video.
 */
(function () {
    'use strict';

    var FACADE_SELECTOR = '.djangocms-video-facade';
    var POSTER_SELECTOR = '.djangocms-video-facade__poster';
    var IFRAME_ATTRIBUTES = {
        frameborder: '0',
        allowfullscreen: 'true',
        allow: 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share',
        referrerpolicy: 'strict-origin-when-cross-origin'
    };

    function warn(message, element) {
        if (window.console && window.console.warn) {
            window.console.warn('djangocms-video: ' + message, element);
        }
    }

    /*
     * YouTube's maxresdefault thumbnail does not exist for every video, so the
     * poster carries an ordered list of fallbacks to try when one fails.
     */
    function attachPosterFallback(poster) {
        var fallbacks = (poster.getAttribute('data-fallback-src') || '')
            .split(/\s+/)
            .filter(Boolean);

        poster.addEventListener('error', function () {
            var next = fallbacks.shift();
            if (next) {
                poster.src = next;
            } else {
                // Nothing left to try. Hide the broken image rather than
                // leaving the browser's placeholder over the play button.
                poster.classList.add('is-unavailable');
            }
        });
    }

    function editorAttributes(facade) {
        var raw = facade.getAttribute('data-video-attributes');
        if (!raw) {
            return {};
        }
        try {
            return JSON.parse(raw) || {};
        } catch (error) {
            warn('could not parse data-video-attributes: ' + error.message, facade);
            return {};
        }
    }

    function play(facade) {
        var src = facade.getAttribute('data-video-src');
        if (!src) {
            warn('facade has no data-video-src, cannot play', facade);
            return;
        }

        var iframe = document.createElement('iframe');
        var attributes = editorAttributes(facade);
        var name;

        for (name in IFRAME_ATTRIBUTES) {
            if (Object.prototype.hasOwnProperty.call(IFRAME_ATTRIBUTES, name)) {
                iframe.setAttribute(name, IFRAME_ATTRIBUTES[name]);
            }
        }
        for (name in attributes) {
            if (Object.prototype.hasOwnProperty.call(attributes, name)) {
                iframe.setAttribute(name, attributes[name]);
            }
        }
        iframe.setAttribute('src', src);
        iframe.setAttribute('title', facade.getAttribute('data-video-title') || '');

        // Insert the player before removing the poster. A third party
        // MutationObserver (cookie banners are common offenders) that throws
        // while we tear the poster down must not leave the plugin empty.
        facade.appendChild(iframe);
        var child;
        while ((child = facade.firstChild) && child !== iframe) {
            facade.removeChild(child);
        }
        facade.classList.add('is-playing');
        // Move focus into the player so keyboard users land on the controls.
        iframe.focus();
    }

    function init(root) {
        var facades = (root || document).querySelectorAll(FACADE_SELECTOR);

        Array.prototype.forEach.call(facades, function (facade) {
            if (facade.getAttribute('data-video-ready')) {
                return;
            }
            facade.setAttribute('data-video-ready', '1');

            var poster = facade.querySelector(POSTER_SELECTOR);
            if (poster) {
                attachPosterFallback(poster);
            }

            facade.addEventListener('click', function () {
                play(facade);
            });
        });
    }

    // Exposed so that content injected after load (django CMS structure board,
    // ajax rendered listings) can initialise its own players.
    window.djangocmsVideoFacade = { init: init };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            init();
        });
    } else {
        init();
    }
}());
