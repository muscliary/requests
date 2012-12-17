# -*- coding: utf-8 -*-

"""
requests.session
~~~~~~~~~~~~~~~~

This module provides a Session object to manage and persist settings across
requests (cookies, auth, proxies).

"""

from copy import deepcopy
from .compat import cookielib
from .cookies import cookiejar_from_dict, remove_cookie_by_name
from .defaults import defaults
from .models import Request
from .hooks import dispatch_hook
from .utils import header_expand, from_key_val_list
from .packages.urllib3.poolmanager import PoolManager


from .adapters import HTTPAdapter

def merge_kwargs(local_kwarg, default_kwarg):
    """Merges kwarg dictionaries.

    If a local key in the dictionary is set to None, it will be removed.
    """

    if default_kwarg is None:
        return local_kwarg

    if isinstance(local_kwarg, str):
        return local_kwarg

    if local_kwarg is None:
        return default_kwarg

    # Bypass if not a dictionary (e.g. timeout)
    if not hasattr(default_kwarg, 'items'):
        return local_kwarg

    default_kwarg = from_key_val_list(default_kwarg)
    local_kwarg = from_key_val_list(local_kwarg)

    # Update new values.
    kwargs = default_kwarg.copy()
    kwargs.update(local_kwarg)

    # Remove keys that are set to None.
    for (k, v) in local_kwarg.items():
        if v is None:
            del kwargs[k]

    return kwargs


class Session(object):
    """A Requests session."""

    __attrs__ = [
        'headers', 'cookies', 'auth', 'timeout', 'proxies', 'hooks',
        'params', 'config', 'verify', 'cert', 'prefetch']

    def __init__(self,
        headers=None,
        cookies=None,
        auth=None,
        timeout=None,
        proxies=None,
        hooks=None,
        params=None,
        config=None,
        prefetch=True,
        verify=True,
        cert=None):

        #: A case-insensitive dictionary of headers to be sent on each
        #: :class:`Request <Request>` sent from this
        #: :class:`Session <Session>`.
        self.headers = from_key_val_list(headers or [])

        #: Authentication tuple or object to attach to
        #: :class:`Request <Request>`.
        self.auth = auth

        #: Float describing the timeout of the each :class:`Request <Request>`.
        self.timeout = timeout

        #: Dictionary mapping protocol to the URL of the proxy (e.g.
        #: {'http': 'foo.bar:3128'}) to be used on each
        #: :class:`Request <Request>`.
        self.proxies = from_key_val_list(proxies or [])

        #: Event-handling hooks.
        self.hooks = from_key_val_list(hooks or {})

        #: Dictionary of querystring data to attach to each
        #: :class:`Request <Request>`. The dictionary values may be lists for
        #: representing multivalued query parameters.
        self.params = from_key_val_list(params or [])

        #: Dictionary of configuration parameters for this
        #: :class:`Session <Session>`.
        self.config = from_key_val_list(config or {})

        #: Prefetch response content.
        self.prefetch = prefetch

        #: SSL Verification.
        self.verify = verify

        #: SSL certificate.
        self.cert = cert

        for (k, v) in list(defaults.items()):
            self.config.setdefault(k, deepcopy(v))

        # Set up a CookieJar to be used by default
        if isinstance(cookies, cookielib.CookieJar):
            self.cookies = cookies
        else:
            self.cookies = cookiejar_from_dict(cookies)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        pass

    def request(self, method, url,
        params=None,
        data=None,
        headers=None,
        cookies=None,
        files=None,
        auth=None,
        timeout=None,
        allow_redirects=True,
        proxies=None,
        hooks=None,
        return_response=True,
        config=None,
        prefetch=None,
        verify=None,
        cert=None):

        req = Request()
        req.method = method
        req.url = url
        req.headers = headers
        req.files = files
        req.data = data
        req.params = params
        req.auth = auth
        req.cookies = cookies
        # TODO: move to attached
        req.allow_redirects = allow_redirects
        req.proxies = proxies
        req.hooks = hooks

        prep = req.prepare()

        # TODO: prepare cookies.

        return self.send(prep)




    def old_request(self, method, url,
        params=None,
        data=None,
        headers=None,
        cookies=None,
        files=None,
        auth=None,
        timeout=None,
        allow_redirects=True,
        proxies=None,
        hooks=None,
        return_response=True,
        config=None,
        prefetch=None,
        verify=None,
        cert=None):

        """Constructs and sends a :class:`Request <Request>`.
        Returns :class:`Response <Response>` object.

        :param method: method for the new :class:`Request` object.
        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
        :param data: (optional) Dictionary or bytes to send in the body of the :class:`Request`.
        :param headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
        :param cookies: (optional) Dict or CookieJar object to send with the :class:`Request`.
        :param files: (optional) Dictionary of 'filename': file-like-objects for multipart encoding upload.
        :param auth: (optional) Auth tuple or callable to enable Basic/Digest/Custom HTTP Auth.
        :param timeout: (optional) Float describing the timeout of the request.
        :param allow_redirects: (optional) Boolean. Set to True by default.
        :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
        :param return_response: (optional) If False, an un-sent Request object will returned.
        :param config: (optional) A configuration dictionary. See ``request.defaults`` for allowed keys and their default values.
        :param prefetch: (optional) whether to immediately download the response content. Defaults to ``True``.
        :param verify: (optional) if ``True``, the SSL cert will be verified. A CA_BUNDLE path can also be provided.
        :param cert: (optional) if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.
        """

        method = str(method).upper()

        # Default empty dicts for dict params.
        data = [] if data is None else data
        files = [] if files is None else files
        headers = {} if headers is None else headers
        params = {} if params is None else params
        hooks = {} if hooks is None else hooks
        prefetch = prefetch if prefetch is not None else self.prefetch

        # use session's hooks as defaults
        for key, cb in list(self.hooks.items()):
            hooks.setdefault(key, cb)

        # Expand header values.
        if headers:
            for k, v in list(headers.items() or {}):
                headers[k] = header_expand(v)

        args = dict(
            method=method,
            url=url,
            data=data,
            params=from_key_val_list(params),
            headers=from_key_val_list(headers),
            cookies=cookies,
            files=files,
            auth=auth,
            hooks=from_key_val_list(hooks),
            timeout=timeout,
            allow_redirects=allow_redirects,
            proxies=from_key_val_list(proxies),
            config=from_key_val_list(config),
            prefetch=prefetch,
            verify=verify,
            cert=cert,
            _poolmanager=self.poolmanager
        )

        # merge session cookies into passed-in ones
        dead_cookies = None
        # passed-in cookies must become a CookieJar:
        if not isinstance(cookies, cookielib.CookieJar):
            args['cookies'] = cookiejar_from_dict(cookies)
            # support unsetting cookies that have been passed in with None values
            # this is only meaningful when `cookies` is a dict ---
            # for a real CookieJar, the client should use session.cookies.clear()
            if cookies is not None:
                dead_cookies = [name for name in cookies if cookies[name] is None]
        # merge the session's cookies into the passed-in cookies:
        for cookie in self.cookies:
            args['cookies'].set_cookie(cookie)
        # remove the unset cookies from the jar we'll be using with the current request
        # (but not from the session's own store of cookies):
        if dead_cookies is not None:
            for name in dead_cookies:
                remove_cookie_by_name(args['cookies'], name)

        # Merge local kwargs with session kwargs.
        for attr in self.__attrs__:
            # we already merged cookies:
            if attr == 'cookies':
                continue

            session_val = getattr(self, attr, None)
            local_val = args.get(attr)
            args[attr] = merge_kwargs(local_val, session_val)

        # Arguments manipulation hook.
        args = dispatch_hook('args', args['hooks'], args)

        # Create the (empty) response.
        r = Request(**args)

        # Give the response some context.
        r.session = self

        # Don't send if asked nicely.
        if not return_response:
            return r

        # Send the HTTP Request.
        return self._send_request(r, **args)

    def get(self, url, **kwargs):
        """Sends a GET request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        kwargs.setdefault('allow_redirects', True)
        return self.request('get', url, **kwargs)

    def options(self, url, **kwargs):
        """Sends a OPTIONS request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        kwargs.setdefault('allow_redirects', True)
        return self.request('options', url, **kwargs)

    def head(self, url, **kwargs):
        """Sends a HEAD request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        kwargs.setdefault('allow_redirects', False)
        return self.request('head', url, **kwargs)

    def post(self, url, data=None, **kwargs):
        """Sends a POST request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary or bytes to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        return self.request('post', url, data=data, **kwargs)

    def put(self, url, data=None, **kwargs):
        """Sends a PUT request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary or bytes to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        return self.request('put', url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        """Sends a PATCH request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary or bytes to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        return self.request('patch', url,  data=data, **kwargs)

    def delete(self, url, **kwargs):
        """Sends a DELETE request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        return self.request('delete', url, **kwargs)

    def send(self, request):
        """Send a given PreparedRequest."""
        adapter = HTTPAdapter()
        r = adapter.send(request)
        return r

    def __getstate__(self):
        return dict((attr, getattr(self, attr, None)) for attr in self.__attrs__)

    def __setstate__(self, state):
        for attr, value in state.items():
            setattr(self, attr, value)

        self.init_poolmanager()


def session(**kwargs):
    """Returns a :class:`Session` for context-management."""

    return Session(**kwargs)
