#!/usr/bin/python
"""fontsquirrel"""

import json
import re
import time
import urllib
import requests
from progressbar import ProgressBar, Percentage, Bar

class FontSquirrel(object):
    """FontSquirrel class"""

    def __init__(self, infile=None, outfile=None, level='basic', config=None):
        """Class constructor"""

        self.domain = 'www.fontsquirrel.com'
        self.url = 'https://%s' % (self.domain)
        self.endpoint = '%s/tools' % (self.url)
        self.language = 'en-US,en;q=0.8'
        self.encoding = 'gzip, deflate, sdch, br'
        self.connection = 'keep-alive'
        self.user_agent = 'Mozilla/2.0 (compatible; MSIE 3.0; Windows 3.1)'
        self.headers = {
            'Accept-Encoding': self.encoding,
            'Accept-Language': self.language,
            'Connection': self.connection,
            'Host': self.domain,
            'Origin': self.url,
            'Referer': '%s/webfont-generator' % (self.endpoint),
            'User-Agent': self.user_agent
        }
        self.cookies = {
            'sitetoken': self.font_sitetoken()
        }
        self.delay = 2

        token = self.font_upload(infile)

        if not token:
            raise Exception('Could not upload %s' % (infile))
            return

        if not self.font_generate(token, level, config):
            raise Exception('Could not generate new font')
            return

        self.font_check(token)
        self.font_download(token, outfile, level, config)

    def font_sitetoken(self):
        """Retrieve sitetoken"""

        request = requests.get('%s/webfont-generator' % (self.endpoint))

        return re.findall('sitetoken=([a-zA-Z0-9]+);', request.headers['Set-Cookie'])[0]

    def font_data(self, token='', level='basic', opts=None):
        """Generate POST data"""

        data = [
            ('dirname[]', token),
            ('mode', level)
        ]

        if not opts:
            opts = {}

        # Font Formats
        formats_options = ['ttf', 'woff', 'woff2', 'eot', 'eotz', 'svg']

        if level in ['basic', 'optimal']:
            opts.update({
                'formats': ['woff', 'woff2']
            })

        for fmt in opts['formats']:
            if fmt in formats_options:
                data.append(('formats[]', fmt))

        # Truetype Hinting
        tt_instructor_options = ['default', 'keep', 'ttfautohint']

        if level in ['basic', 'optimal']:
            opts.update({
                'tt_instructor': 'default'
            })

        if 'tt_instructor' in opts:
            if opts['tt_instructor'] in tt_instructor_options:
                data.append(('tt_instructor', opts['tt_instructor']))

        # Rendering
        fix_gasp_options = [True, False]
        remove_kerning_options = [True, False]

        if level in ['basic', 'optimal']:
            opts.update({
                'fix_gasp': True
            })

        if 'fix_gasp' in opts:
            if opts['fix_gasp'] in fix_gasp_options:
                data.append(('fix_gasp', 'xy' if opts['fix_gasp'] is True else ''))

        if 'remove_kerning' in opts:
            if opts['remove_kerning'] in remove_kerning_options:
                data.append(('remove_kerning', 'y' if opts['remove_kerning'] is True else ''))

        # Vertical Metrics
        fix_vertical_metrics_options = [True, False]

        if level in ['basic', 'optimal']:
            opts.update({
                'fix_vertical_metrics': True,
                'metrics_ascent': None,
                'metrics_descent': None,
                'metrics_linegap': None
            })

        if 'fix_vertical_metrics' in opts:
            if ('metrics_ascent' in opts and opts['metrics_ascent'] != None) or ('metrics_descent' in opts and opts['metrics_descent'] != None) or ('metrics_linegap' in opts and opts['metrics_linegap'] != None):
                data.append(('fix_vertical_metrics', 'C'))
            else:
                if opts['fix_vertical_metrics'] in fix_vertical_metrics_options:
                    data.append(('fix_vertical_metrics', 'Y' if opts['fix_vertical_metrics'] is True else 'N'))

            if 'metrics_ascent' in opts:
                if opts['metrics_ascent'] is None or isinstance(opts['metrics_ascent'], int):
                    data.append(('metrics_ascent', str(opts['metrics_ascent']) if opts['metrics_ascent'] != None else ''))

            if 'metrics_descent' in opts:
                if opts['metrics_descent'] is None or isinstance(opts['metrics_descent'], int):
                    data.append(('metrics_descent', str(opts['metrics_descent']) if opts['metrics_descent'] != None else ''))

            if 'metrics_linegap' in opts:
                if opts['metrics_linegap'] is None or isinstance(opts['metrics_linegap'], int):
                    data.append(('metrics_linegap', str(opts['metrics_linegap']) if opts['metrics_linegap'] != None else ''))

        # Fix Missing Glyphs
        add_spaces_options = [True]
        add_hyphens_options = [True]

        if level in ['basic', 'optimal']:
            opts.update({
                'add_spaces': True,
                'add_hyphens': True
            })

        if 'add_spaces' in opts:
            if opts['add_spaces'] in add_spaces_options:
                data.append(('add_spaces', 'Y'))

        if 'add_hyphens' in opts:
            if opts['add_hyphens'] in add_hyphens_options:
                data.append(('add_hyphens', 'Y'))

        # X-height Matching
        x_height_matching_options = ['none', 'custom', 'arial', 'verdana', 'trebuchet', 'georgia', 'times', 'courier']

        if level in ['basic', 'optimal']:
            opts.update({
                'fallback': 'none',
                'fallback_custom': 100
            })

        if 'fallback' in opts:
            if opts['fallback'] in x_height_matching_options:
                data.append(('fallback', opts['fallback']))

        if 'fallback' not in opts:
            opts.update({
                'fallback': 'none'
            })

        if 'fallback_custom' in opts:
            if isinstance(opts['fallback_custom'], int):
                opts.update({
                    'fallback_custom': opts['fallback_custom']
                })

        if 'fallback_custom' not in opts:
            opts.update({
                'fallback_custom': 100
            })

        data.append(('fallback', opts['fallback']))
        data.append(('fallback_custom', str(opts['fallback_custom'])))

        # Protection
        protection_options = [True]

        if 'webonly' in opts:
            if opts['webonly'] in protection_options:
                data.append(('webonly', 'Y'))

        # Subsetting
        options_subset_options = ['basic', 'advanced', 'none']
        subset_range_options = [
            'macroman',

            'lowercase', 'currency', 'accentedlower',
            'uppercase', 'typographics', 'accentedupper',
            'numbers', 'math', 'diacriticals',
            'punctuation', 'altpunctuation',

            'albanian', 'faroese', 'maltese',
            'bosnian', 'french', 'norwegian',
            'catalan', 'georgian', 'polish',
            'croatian', 'german', 'portuguese',
            'cyrillic', 'greek', 'romanian',
            'czech', 'hebrew', 'serbian',
            'danish', 'hungarian', 'slovak',
            'dutch', 'icelandic', 'slovenian',
            'english', 'italian', 'spanish',
            'esperanto', 'latvian', 'swedish',
            'estonian', 'lithuanian', 'turkish',
            'malagasy',

            'ubasic', 'upunctuation', 'ulatinb',
            'ulatin1', 'ulatina',
            'ucurrency', 'ulatinaddl'
        ]

        if level in ['basic', 'optimal']:
            opts.update({
                'options_subset': 'basic',
                'subset_custom': None,
                'subset_custom_range': None,
                'subset_ot_features_list': None
            })

        if 'options_subset' in opts and opts['options_subset'] in options_subset_options:
            data.append(('options_subset', opts['options_subset']))

        if 'subset_range' in opts and isinstance(opts['subset_range'], list):
            for subset in opts['subset_range']:
                if subset in subset_range_options:
                    data.append(('subset_range[]', subset))

        if 'subset_custom' in opts:
            if opts['subset_custom'] is None:
                data.append(('subset_custom', ''))
            elif isinstance(opts['subset_custom'], str):
                data.append(('subset_custom', opts['subset_custom']))

        if 'subset_custom_range' in opts:
            if opts['subset_custom_range'] is None:
                data.append(('subset_custom_range', ''))
            elif isinstance(opts['subset_custom_range'], str):
                data.append(('subset_custom_range', opts['subset_custom_range']))

        if 'subset_ot_features_list' in opts:
            if opts['subset_ot_features_list'] is None:
                data.append(('subset_ot_features_list', ''))
            elif isinstance(opts['subset_ot_features_list'], str):
                data.append(('subset_ot_features_list', opts['subset_ot_features_list']))

        # OpenType Features
        subset_ot_features_options = [True]

        if 'subset_ot_features' in opts and opts['subset_ot_features'] in subset_ot_features_options:
            data.append(('subset_ot_features', 'all'))

        if 'subset_ot_features_list' in opts and isinstance(opts['subset_ot_features_list'], str):
            data.append(('subset_ot_features', opts['subset_ot_features_list']))

        # OpenType Flattening
        ot_features_options = [
            'smcp',
            'c2sc',
            'onum',
            'lnum',
            'tnum',
            'pnum',
            'zero',
            'salt',

            'ss01', 'ss11',
            'ss02', 'ss12',
            'ss03', 'ss13',
            'ss04', 'ss14',
            'ss05', 'ss15',
            'ss06', 'ss16',
            'ss07', 'ss17',
            'ss08', 'ss18',
            'ss09', 'ss19',
            'ss10', 'ss20'
        ]

        if 'ot_features' in opts and isinstance(opts['ot_features'], list):
            for feature in opts['ot_features']:
                if feature in ot_features_options:
                    data.append(('ot_features[]', feature))

        # CSS
        base64_options = [True]
        style_link_options = [True]

        if 'base64' in opts:
            if opts['base64'] in base64_options:
                data.append(('base64', 'Y'))

        if 'style_link' in opts:
            if opts['style_link'] in style_link_options:
                data.append(('style_link', 'Y'))

        if 'css_stylesheet' in opts and isinstance(opts['css_stylesheet'], str):
            data.append(('css_stylesheet', opts['css_stylesheet']))
        else:
            data.append(('css_stylesheet', 'stylesheet.css'))

        # Advanced Options
        if level in ['basic', 'optimal']:
            opts.update({
                'filename_suffix': '-webfont',
                'emsquare': 2048,
                'spacing_adjustment': 0
            })

        if 'filename_suffix' in opts and isinstance(opts['filename_suffix'], str):
            data.append(('filename_suffix', opts['filename_suffix']))

        if 'emsquare' in opts and isinstance(opts['emsquare'], str):
            data.append(('emsquare', str(opts['emsquare'])))

        if 'spacing_adjustment' in opts and isinstance(opts['spacing_adjustment'], str):
            data.append(('spacing_adjustment', str(opts['spacing_adjustment'])))

        # Shortcuts
        rememberme_options = [True]

        if 'rememberme' in opts and opts['rememberme'] in rememberme_options:
            data.append(('rememberme', 'Y'))

        # Agreement
        data.append(('agreement', 'Y'))

        # ID
        data.append(('id', token))

        return urllib.urlencode(data)

    def font_upload(self, font=''):
        """Upload font"""

        headers = self.headers
        headers.update({
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        })

        files = {
            'file': open(font, 'rb')
        }

        print 'Uploading %s...' % (font)

        request = requests.post('%s/upload' % (self.endpoint), headers=headers, cookies=self.cookies, files=files)
        data = json.loads(request.text)

        try:
            token = data['font']['token']
        except KeyError:
            return None

        return token

    def font_generate(self, token='', level='basic', config=None):
        """Generate new font"""

        headers = self.headers
        headers.update({
            'Accept': 'text/plain, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        })

        if not config:
            config = {}

        data = self.font_data(token, level, config)

        print 'Generating fonts...'

        request = requests.post('%s/generate' % (self.endpoint), headers=headers, cookies=self.cookies, data=data)

        try:
            data = json.loads(request.text)
        except ValueError:
            return True

        return False

    def font_progress(self, token=''):
        """Check on font progress"""

        request = requests.get('%s/progress/%s' % (self.endpoint, token), headers=self.headers, cookies=self.cookies)

        return json.loads(request.text)

    def font_check(self, token=''):
        """Check font progress at regular interval"""
        print 'Processing...'

        widgets = [Percentage(), ' ', Bar()]
        progress_bar = ProgressBar(widgets=widgets, maxval=100).start()

        progress_percent = 0

        while progress_percent != 100:
            progress = self.font_progress(token)
            progress_percent = int(progress['progress'])
            progress_bar.update(progress_percent)

            if progress_percent == 100:
                break

            time.sleep(self.delay)

    def font_download(self, token='', outfile=None, level='basic', config=None):
        """Download font"""

        headers = self.headers
        headers.update({
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        })

        if not config:
            config = {}

        data = self.font_data(token, level, config)

        request = requests.post('%s/download' % (self.endpoint), headers=headers, cookies=self.cookies, data=data)
        filesize = int(request.headers['Content-Length']) * 1024

        if not outfile:
            outfile = re.findall('filename="(.*)"', request.headers['Content-Disposition'])[0]

        chunks = 0
        chunk_size = 2048

        print 'Downloading...'

        widgets = [Percentage(), ' ', Bar()]
        progress_bar = ProgressBar(widgets=widgets, maxval=filesize).start()

        with open(outfile, 'wb') as outfile:
            for chunk in request.iter_content(chunk_size):
                chunks += chunk_size
                progress_bar.update(chunks)

                outfile.write(chunk)
