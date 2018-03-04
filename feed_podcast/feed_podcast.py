# -*- coding: utf-8 -*-
"""
Feed Podcast Summary
====================

This plugin allows feeds to be generated with a podcast format.
"""

from __future__ import unicode_literals

import logging
import os

from jinja2 import Markup

from pelican import signals
from pelican.writers import Writer
from pelican.utils import is_selected_for_writing
from pelican.utils import set_date_tzinfo
from pelican.utils import path_to_url
from pelican.utils import get_relative_path

from feedgen.feed import FeedGenerator

from .magic_set import magic_set

import six
if not six.PY3:
    from urlparse import urlparse
else:
    from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class PodcastWriter(Writer):
    # TODO the proper way to do this would be to add the feed
    # to ArticlesGenerator.generate_feeds

    def _create_new_feed(self, feed_type, feed_title, context):
        #feed_class = FeedGenerator
        if feed_title:
            feed_title = context['SITENAME'] + ' - ' + feed_title
        else:
            feed_title = context['SITENAME']
        feed = FeedGenerator()
        feed.id('http://eldesarmador.org/media/4242')
        feed.rights('cc-by-nc')
        feed.title(feed_title)
        feed.link(href='http://eldesarmador.org/podcast.xml', rel='self')
        feed.author({'name': 'La Imilla Hacker', 'email': 'imilla.hacker@riseup.net'})
        feed.logo('https://eldesarmador.org/theme/img/imilla_hacker_1.png')
        feed.icon('https://eldesarmador.org/theme/img/imilla_hacker_1.png')
        feed.subtitle('Un programa sobre tecnologia y libertad')
        feed.language('es')
        # TODO GET FROM CONFIG
        # description=context.get('SITESUBTITLE', ''))
        return feed

    def _load_podcast(self, feed):
        feed.load_extension('podcast', atom=True)
        feed.podcast.itunes_category('Technology', 'Podcasting')
        feed.podcast.itunes_author('La Imilla Hacker')
        feed.podcast.itunes_explicit('no')
        feed.podcast.itunes_complete('no')
        return feed


    def _add_item_to_the_feed(self, feed, item):
        title = Markup(item.title).striptags()

        link = '%s/%s' % (self.site_url, item.url)
        description = item.podcastsummary if hasattr(item, 'podcastsummary') else ''
        date = item.date
        
        try:
            audio = item.audio
        except:
            print("no audio, no entry!")
            return

        print("processing", link)

        entry = feed.add_entry()
        entry.id(link)
        entry.title(title)
        entry.updated(date)
        if six.PY3:
            entry.description({'type': 'xhtml', 'content': description})
        else:
            entry.description(description)
        entry.enclosure(audio, 0, 'audio/mpeg')

    def write_feed(self, elements, context, path=None, feed_type='atom',
                   override_output=False, feed_title=None):
        """Generate a feed with the list of articles provided

        Return the feed. If no path or output_path is specified, just
        return the feed object.

        :param elements: the articles to put on the feed.
        :param context: the context to get the feed metadata.
        :param path: the path to output.
        :param feed_type: the feed type to use (atom or rss)
        :param override_output: boolean telling if we can override previous
            output with the same name (and if next files written with the same
            name should be skipped to keep that one)
        :param feed_title: the title of the feed.o
        """
        if not is_selected_for_writing(self.settings, path):
            return

        self.site_url = context.get(
            'SITEURL', path_to_url(get_relative_path(path)))

        self.feed_domain = context.get('FEED_DOMAIN')
        self.feed_url = '{}/{}'.format(self.feed_domain, path)

        feed = self._create_new_feed(feed_type, feed_title, context)

        max_items = len(elements)
        if self.settings['FEED_MAX_ITEMS']:
            max_items = min(self.settings['FEED_MAX_ITEMS'], max_items)
        for i in range(max_items):
            self._add_item_to_the_feed(feed, elements[i])


        feed = self._load_podcast(feed)

        if path:
            complete_path = os.path.join(self.output_path, path)
            try:
                os.makedirs(os.path.dirname(complete_path))
            except Exception:
                pass

            encoding = 'utf-8' if six.PY3 else None
            logger.info('Writing %s', complete_path)
            
            feed.atom_file(complete_path, pretty=True, encoding=encoding)
            print("done")
            signals.feed_written.send(
                complete_path, context=context, feed=feed)

        return feed


def set_feed_use_summary_default(pelican_object):
    # modifying DEFAULT_CONFIG doesn't have any effect at this point in pelican setup
    # everybody who uses DEFAULT_CONFIG is already used/copied it or uses the pelican_object.settings copy.

    pelican_object.settings.setdefault('FEED_USE_SUMMARY', False)

def patch_pelican_writer(pelican_object):
    @magic_set(pelican_object)
    def get_writer(self):
        return PodcastWriter(self.output_path,settings=self.settings)

def register():
    signals.initialized.connect(set_feed_use_summary_default)
    signals.initialized.connect(patch_pelican_writer)
