import httpx

class MarimoStream:
    HOP_BY_HOP_HEADERS = {
        'connection',
        'keep-alive',
        'proxy-authenticate',
        'proxy-authorization',
        'te',
        'trailers',
        'transfer-encoding',
        'upgrade',
    }
    EXCLUDE_HEADERS = {
        'host',
        'content-length'
    }
    def __init__(self, request, url):
        self.url = url
        self.request = request
        self.status_code = None
        self.content_type = None
        self.exclude_headers = self.EXCLUDE_HEADERS.union(self.HOP_BY_HOP_HEADERS)
        self.headers = {k: v for k, v in request.headers.items() if k.lower() not in self.exclude_headers}

    def __iter__(self):
        with httpx.Client() as client:
            with client.stream(
                    method=self.request.method,
                    url=self.url,
                    headers=self.headers,
                    params=self.request.GET,
                    data=self.request.body,
            ) as resp:
                self.status_code = resp.status_code
                self.content_type = resp.headers.get('Content-Type', 'text/html')
                yield from resp.iter_bytes()