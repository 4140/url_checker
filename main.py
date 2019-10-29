"""Check target of shortened urls."""
import requests
from urllib.parse import urlparse


SUPPORTED_HOSTS = (
    'bit.ly',
    'tinyurl.com',
    't.co',
)


class URLChecker(object):
    """Compile a list of expanded URL from source of shortened ones."""

    def __init__(self, file_path, *args, **kwargs):
        """Set up object variables."""
        self.file_path = file_path

    def expand_url(self, url):
        """Resolve target of a single shortened URL."""
        parsed_url = urlparse(url)
        if parsed_url.hostname not in SUPPORTED_HOSTS:
            return

        r = requests.head(url)
        location = r.headers.get('Location') or r.headers.get('location')

        if location and location != url:
            return location

    def process_list(self, url_list):
        """Expand individual URLs from list."""
        for url in url_list:
            yield self.expand_url(url)

    def handle_file(self):
        """Handle a simple file containing one URL per line."""
        with open(self.file_path, newline='\n') as file:
            return self.process_list(file.read().splitlines())
