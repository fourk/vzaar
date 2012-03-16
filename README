##python-vzaar
This is a wrapper for Vzaar's version 1.0 API. As of this repository's initial
commit, all documented API methods are implemented.

The most up-to-date version of this code will be available at https://github.com/fourk/vzaar

The original API documentation can be found at http://developer.vzaar.com/docs/version_1.0/

###Usage:

Install using setuptools, pip, or by cloning the repository and running:

    python setup.py intall

Once installed, it can be used with:

    from vzaar import Vzaar
    api = Vzaar(username, api_key, video_sucess_redirect, max_video_size)

    api.user_details(username)

If you're using django, you can define the values in your settings object instead
of having to set them when you instantiate the api object. Add each of the following
to your settings, then import DjangoVzaar instead of importing Vzaar.

    VZAAR_USERNAME - string - your username (not your email)
    VZAAR_KEY - string - Vzaar API key
    VIDEO_SUCCESS_REDIRECT - string - where to redirect a user after upload
            ex: http://example.com/callback/
    MAX_VIDEO_SIZE - integer - size (in bytes) of maximum alowed upload size

    from vzaar import DjangoVzaar
    api = DjangoVzaar()

##Dependencies

  * oauth2 - https://github.com/simplegeo/python-oauth2
  * httplib2 - http://code.google.com/p/httplib2/
  * python2.6 - This has been tested using python 2.6 - You may be able to get
         it to work in 2.5 by installing the json module that comes packaged
         with python 2.6, or the simplejson module.
