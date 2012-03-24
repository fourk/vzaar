__version__ = '1.0.5'
__author__ = "James Burkhart"

import oauth2 as oauth
import urllib
import json
import time
import httplib2
from xml.dom.minidom import parseString, Document

"""
The Vzaar object expects to be instantiated with the following positional arguments
    vzaar_username - string - your username (not your email)
    vzaar_key - string - Vzaar API key
    video_success_redirect - string - where to redirect a user after upload
            ex: http://example.com/callback/ (or a callable that returns a string)
    max_video_size - integer - size (in bytes) of maximum alowed upload size

    If you're using django, simply set a value for each of the above keys in
    your settings.py file (convert to uppercase, i.e. VZAAR_KEY) and import
    DjangoVzaar instead of Vzaar
"""

class dict2xml(object):
    """
    dict2xml code from http://stackoverflow.com/a/6262732/458095
    """
    doc = Document()

    def __init__(self, structure):
        if len(structure) == 1:
            rootName = str(structure.keys()[0])
            self.root = self.doc.createElement(rootName)

            self.doc.appendChild(self.root)
            self.build(self.root, structure[rootName])

    def build(self, father, structure):
        if type(structure) == dict:
            for k in structure:
                tag = self.doc.createElement(k)
                father.appendChild(tag)
                self.build(tag, structure[k])

        elif type(structure) == list:
            grandFather = father.parentNode
            tagName = father.tagName
            grandFather.removeChild(father)
            for ll in structure:
                tag = self.doc.createElement(tagName)
                self.build(tag, ll)
                grandFather.appendChild(tag)

        else:
            data = str(structure)
            tag = self.doc.createTextNode(data)
            father.appendChild(tag)

    def display(self):
        print self.doc.toprettyxml(indent="  ")

class Vzaar(object):
    def __init__(self, vzaar_username, vzaar_key, video_success_redirect,
            max_video_size):

        self.VIDEO_SUCCESS_REDIRECT = video_success_redirect
        if hasattr(self.VIDEO_SUCCESS_REDIRECT, '__call__'):
            self.VIDEO_SUCCESS_REDIRECT = self.VIDEO_SUCCESS_REDIRECT()
        self.MAX_VIDEO_SIZE = max_video_size
        self.token = oauth.Token(key=vzaar_username,
                secret=vzaar_key)
        self.consumer = oauth.Consumer(key='', secret='')
        self.base_url = 'http://vzaar.com/api/%s'
        self.http_client = httplib2.Http()

    def _prepare_request(self, method, uri, parameters):
        req = oauth.Request(method=method, url=uri, parameters=parameters)
        signature_method = oauth.SignatureMethod_HMAC_SHA1()
        req.sign_request(signature_method, self.consumer, self.token)
        return req

    def _prepare_post_data(self, post_data):
        if post_data is None:
            post_data = {}
        post_data = {'vzaar-api': post_data}
        post_data = dict2xml(post_data)
        xml = post_data.doc.toxml()
        post_data.doc.unlink()
        return xml

    def _prepare_parameters(self, extra_params):
        params = {
                'oauth_version': '1.0',
                'oauth_nonce': oauth.generate_nonce(),
                'oauth_timestamp': int(time.time()),
            }
        if extra_params is not None:
            params.update(extra_params)
        return params

    def _get_realm_from_uri(self, uri):
        schema, rest = urllib.splittype(uri)
        if rest.startswith('//'):
            hierpart = '//'
        else:
            hierpart = ''
        host, rest = urllib.splithost(rest)
        realm = schema + ':' + hierpart + host

        return realm

    def _make_call(self, endpoint, method='GET', extra_params=None,
            extra_headers=None, post_data=None):
        headers = {}
        if extra_headers is not None:
            headers.update(extra_headers)

        params = self._prepare_parameters(extra_params)

        uri = self.base_url % endpoint
        req = self._prepare_request(method, uri, params)

        if method in ['GET', 'DELETE']:
            uri = req.to_url()
            body = ''
        else:
            headers['Content-Type'] = 'application/xml'
            realm = self._get_realm_from_uri(uri)
            headers.update(req.to_header(realm=realm))
            body = self._prepare_post_data(post_data)

        return httplib2.Http.request(self.http_client, uri, method=method,
                    body=body, headers=headers)

    def _parse_xml(self, body, keys):
        """
        Parameters:
        body - String of xml
        keys - List of strings - keys to be parsed out of the xml document

        Returns a dictionary containing the specified keys and their values.
        """
        document = parseString(body)
        parsed_data = {}

        for key in keys:
            parent = document.getElementsByTagName(key)[0]
            parsed_data[key] = parent.lastChild.nodeValue

        return parsed_data

    def _assert_status(self, response, body, status='200'):
        """Checks if the expected status code was returned - raises exception
        if not."""
        if response.get('status') != '200':
            raise Exception('Error - %s \n--\n %s' % (response, body))

    def account_details(self, account):
        """
        account - integer - corresponds to vzaar account type
        """
        response, body = self._make_call('accounts/%i.json' % account)
        self._assert_status(response, body)
        return json.loads(body)

    def user_details(self, username):
        """
        username - the vzaar login name for the user.
            Note: This must be the actual username and not the email address
        """
        response, body = self._make_call('users/%s.json' % username)
        self._assert_status(response, body)
        return json.loads(body)

    def video_details(self, id, **kwargs):
        """
        REQUIRED:
        id - ex: 912345

        OPTIONAL_KWARGS:
        borderless, boolean - If set to true and the user has sufficient
                            privileges, the size and embeded code returned
                            will be be for a borderless player. Else ignored
        embed_only, boolean - When returning data, only include the minimum
                            fields and embed code possible. Use this if you
                            want the quickest and smallest return code for
                            embedding in it
        http://developer.vzaar.com/docs/version_1.0/public/video_details
        """
        response, body = self._make_call('videos/%s.json' % id,
                extra_params=kwargs)
        self._assert_status(response, body)

        return json.loads(body)


    def video_list(self, username, **kwargs):
        """
        REQUIRED:
        username - vzaar login name for the user.
                Note: This must be the actual username, not the email address

        OPTIONAL:
        count, integer - Specifies the number of videos to retrieve per page.
                Default is 20. Maximum is 100
        page, integer - Specifies the page number to retrieve.
                Default is 1
        sort, string - Values can be asc (least_recent) or desc (most_recent).
                Defaults to desc
        title, string - Return only videos with title containing given string
        """

        response, body = self._make_call('%s/videos.json' % username,
                extra_params=kwargs)
        self._assert_status(response, body)
        return json.loads(body)


    def prepare_upload(self):
        extra_params = {
                'success_action_redirect': self.VIDEO_SUCCESS_REDIRECT,
                'max_file_size': self.MAX_VIDEO_SIZE,
                }
        response, body = self._make_call('videos/signature',
                extra_params=extra_params)
        self._assert_status(response, body)

        keys = ['guid', 'key', 'https', 'acl', 'bucket',
                'policy', 'expirationdate', 'accesskeyid', 'signature']
        data_out = self._parse_xml(body, keys)
        data_out['success_action_redirect'] = extra_params['success_action_redirect']

        return data_out


    def process(self, guid, **kwargs):
        """
        REQUIRED:
        guid string - Specifies the guid to operate on

        OPTIONAL KWARGS:
        title string - Specifies the title for the video
        description string - Specifies the description for the video
        profile integer - Specifies the size for the video to be encoded in.
                If not specified, this will use the vzaar default or the user
                default (if set)
        replace_id integer - Specifies the video ID of an existing video that
                you wish to replace with the new video.
        transcoding boolean - True forces vzaar to transcode the video,
                False makes vzaar use the original source file
                (available only for mp4 and flv files)
        labels string - Comma separated list of labels to be assigned
                to the video

        Profile values
        1. Small
        2. Medium
        3. Large
        4. High Definition
        5. Original
        """
        body_data = {
                'guid': guid,
                'title': 'Untitled',
                'description': 'No description',
        }
        body_data.update(kwargs)
        post_data = {'video': body_data}

        response, body = self._make_call('videos', method="POST",
                post_data=post_data)
        self._assert_status(response, body, '201')

        return self._parse_xml(body, ['video'])


    def delete(self, id):
        """
        REQUIRED:
        id - ex: 912345
        """
        response, body = self._make_call('videos/%s.xml' % id,
                method="DELETE")
        self._assert_status(response, body)

        keys = ['type', 'version', 'title', 'author_name', 'author_url',
                'provider_name', 'provider_url', 'html', 'height', 'width']
        return self._parse_xml(body, keys)


    def edit(self, id, **kwargs):
        """
        REQUIRED:
        id - ex: 912345

        OPTIONAL:
        title string - Specifies the new title for the video
        description string - Specifies the new description for the video
        private boolean (true|false) - Marks the video as private or public
        seo_url string - Specifies the SEO url for the video
        """
        response, body = self._make_call('videos/%s.xml' % id,
                method="PUT", post_data={'video': kwargs})
        self._assert_status(response, body)

        keys = ["type", "version", "title", "author_name", "author_url",
                "provider_name", "provider_url", "html", "height", "width"]
        return self._parse_xml(body, keys)
        return response, body

class DjangoVzaar(Vzaar):
    """
    wrapper for Vzaar api that takes settings from django config file
    """
    def __init__(self):
        from django.conf import settings
        super(DjangoVzaar, self).__init__(settings.VZAAR_USERNAME,
                settings.VZAAR_KEY, settings.VIDEO_SUCCESS_REDIRECT,
                settings.MAX_VIDEO_SIZE)

