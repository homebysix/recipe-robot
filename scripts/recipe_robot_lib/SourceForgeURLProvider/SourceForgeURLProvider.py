#!/usr/bin/env python

import datetime
import re
from xml.dom.minidom import parse, parseString
import urllib2

from autopkglib import Processor, ProcessorError

__all__ = ["SourceForgeURLProvider"]

FILE_INDEX_URL = 'https://sourceforge.net/api/file/index/project-id/%s/rss'

class SourceForgeURLProvider(Processor):
    '''Provides URL to the latest file that matches a pattern for a particular SourceForge project.'''

    input_variables = {
        'SOURCEFORGE_PROJECT_ID': {
            'required': True,
            'description': 'Numerical ID of SourceForge project',
            },
        'SOURCEFORGE_FILE_PATTERN': {
            'required': True,
            'description': 'Pattern to match SourceFile files on',
            },
    }
    output_variables = {
        'url': {
            'description': 'URL to the latest SourceForge project download'
        }
    }

    description = __doc__

    def get_sf_file_url(self, proj_id, pattern):
        flisturl = FILE_INDEX_URL % proj_id

        try:
            f = urllib2.urlopen(flisturl)
            rss = f.read()
            f.close()
        except BaseException as e:
            raise ProcessorError('Could not retrieve RSS feed %s' % flisturl)

        re_file = re.compile(self.env.get('SOURCEFORGE_FILE_PATTERN'), re.I)

        rss_parse = parseString(rss)

        items = []

        for i in  rss_parse.getElementsByTagName('item'):
            pubDate = i.getElementsByTagName('pubDate')[0].firstChild.nodeValue
            link = i.getElementsByTagName('link')[0].firstChild.nodeValue

            pubDatetime = datetime.datetime.strptime(pubDate, '%a, %d %b %Y %H:%M:%S UT')

            if re_file.search(link):
                items.append((pubDatetime, link),)

        items.sort(key=lambda r: r[0])

        if len(items) < 1:
            raise ProcessorError('No matched files')

        return items[-1][1]

    def main(self):
        proj_id  = self.env.get('SOURCEFORGE_PROJECT_ID')
        file_pat = self.env.get('SOURCEFORGE_FILE_PATTERN')

        self.env['url'] = self.get_sf_file_url(proj_id, file_pat)
        self.output('File URL %s' % self.env['url'])

if __name__ == '__main__':
    processor = SourceForgeURLProvider()
    processor.execute_shell()
