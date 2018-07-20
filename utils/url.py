from urllib.parse import urlencode


def url_append_param(url, param):
    param_start = url.find('?')
    if 0 <= param_start < len(url) - 1:
        url += '&'
    else:
        url += '?'
    url += urlencode(param)
    return url
