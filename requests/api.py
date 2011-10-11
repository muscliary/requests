# -*- coding: utf-8 -*-

"""
requests.api
~~~~~~~~~~~~

This module implements the Requests API.

:copyright: (c) 2011 by Kenneth Reitz.
:license: ISC, see LICENSE for more details.

"""

from ._config import get_config
from .models import Request, Response
from .status_codes import codes
from hooks import setup_hooks, dispatch_hooks
from .utils import cookiejar_from_dict, header_expand


__all__ = ('request', 'get', 'head', 'post', 'patch', 'put', 'delete')


def request(method, url,
    params=None, data=None, headers=None, cookies=None, files=None, auth=None,
    timeout=None, allow_redirects=False, proxies=None, hooks=None,
    config=None, _pools=None, _return_request=False):

    """Constructs and sends a :class:`Request <Request>`.
    Returns :class:`Response <Response>` object.

    :param method: method for the new :class:`Request` object.
    :param url: URL for the new :class:`Request` object.
    :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
    :param data: (optional) Dictionary or bytes to send in the body of the :class:`Request`.
    :param headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
    :param cookies: (optional) Dict or CookieJar object to send with the :class:`Request`.
    :param files: (optional) Dictionary of 'filename': file-like-objects for multipart encoding upload.
    :param auth: (optional) AuthObject to enable Basic HTTP Auth.
    :param timeout: (optional) Float describing the timeout of the request.
    :param allow_redirects: (optional) Boolean. Set to True if POST/PUT/DELETE redirect following is allowed.
    :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
    :param _pools: (optional) An HTTP PoolManager to use.
    """

    method = str(method).upper()
    config = get_config(config)

    # cookies = cookiejar_from_dict(cookies if cookies is not None else dict())
    # cookies = cookiejar_from_dict(cookies)

    # Expand header values
    if headers:
        for k, v in headers.items() or {}:
            headers[k] = header_expand(v)

    args = dict(
        method=method,
        url=url,
        data=data,
        params=params,
        headers=headers,
        cookies=cookies,
        files=files,
        auth=auth,
        timeout=timeout or config.get('timeout'),
        hooks=hooks,
        allow_redirects=allow_redirects,
        proxies=proxies or config.get('proxies'),
        _pools=_pools
    )

    hooks = setup_hooks(hooks if hooks is not None else dict())

    # Arguments manipulation hook.
    args = dispatch_hooks(hooks['args'], args)

    # Create Request object.
    r = Request(**args)

    # Pre-request hook.
    r = dispatch_hooks(hooks['pre_request'], r)

    # Only construct the request (for async)
    if _return_request:
        return r

    # Send the HTTP Request.
    r.send()

    # TODO: Add these hooks inline.
    # Post-request hook.
    r = dispatch_hooks(hooks['post_request'], r)

    # Response manipulation hook.
    r.response = dispatch_hooks(hooks['response'], r.response)

    return r.response


def get(url, **kwargs):
    """Sends a GET request. Returns :class:`Response` object.

    :param url: URL for the new :class:`Request` object.
    :param **kwargs: Optional arguments that ``request`` takes.
    """

    if 'allow_redirects' not in kwargs:
        kwargs['allow_redirects'] = True

    return request('get', url, **kwargs)


def head(url, **kwargs):
    """Sends a HEAD request. Returns :class:`Response` object.

    :param url: URL for the new :class:`Request` object.
    :param **kwargs: Optional arguments that ``request`` takes.
    """

    if 'allow_redirects' not in kwargs:
        kwargs['allow_redirects'] = True

    return request('head', url, **kwargs)


def post(url, data='', **kwargs):
    """Sends a POST request. Returns :class:`Response` object.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary or bytes to send in the body of the :class:`Request`.
    :param **kwargs: Optional arguments that ``request`` takes.
    """

    return request('post', url, data=data, **kwargs)


def put(url, data='', **kwargs):
    """Sends a PUT request. Returns :class:`Response` object.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary or bytes to send in the body of the :class:`Request`.
    :param **kwargs: Optional arguments that ``request`` takes.
    """

    return request('put', url, data=data, **kwargs)


def patch(url, data='', **kwargs):
    """Sends a PATCH request. Returns :class:`Response` object.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary or bytes to send in the body of the :class:`Request`.
    :param **kwargs: Optional arguments that ``request`` takes.
    """

    return request('patch', url, data=data, **kwargs)


def delete(url, **kwargs):
    """Sends a DELETE request. Returns :class:`Response` object.

    :param url: URL for the new :class:`Request` object.
    :param **kwargs: Optional arguments that ``request`` takes.
    """

    return request('delete', url, **kwargs)
