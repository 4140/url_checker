"""Check target of shortened urls."""
import aiohttp
import argparse
import asyncio
import email
import quopri
import re

from urllib.parse import urlparse


SUPPORTED_HOSTS = (
    'bit.ly',
    'tinyurl.com',
    't.co',
    'itr-links.stackoverflow.email'
)


class URLChecker(object):
    """Compile a list of expanded URL from source of shortened ones."""

    def __init__(self, file_path, *args, **kwargs):
        """Set up object variables."""
        self.file_path = file_path

        self.queue = asyncio.Queue()

    async def expand_url(self, url, session):
        """Resolve target of a single shortened URL."""
        parsed_url = urlparse(url)
        if parsed_url.hostname not in SUPPORTED_HOSTS:
            return

        async with session.head(url) as r:
            location = (
                r.headers.get('Location') or r.headers.get('location')
            )

            if location and location != url:
                return location

    async def process_list(self, url_list):
        """Expand individual URLs from list."""
        async with aiohttp.ClientSession() as session:
            for url in url_list:
                expanded = await self.expand_url(url, session)
                await self.queue.put(expanded)

    async def handle_file(self):
        """Determine which file type handler to use."""
        if self.file_path.endswith('.eml'):
            await self.handle_eml()
        else:
            await self.handle_txt()

        while not self.queue.empty():
            url = await self.queue.get()
            print(url)

    async def handle_txt(self):
        """Handle a simple file containing one URL per line."""
        with open(self.file_path) as file:
            return await self.process_list(file.read().splitlines())

    async def handle_eml(self):
        """Get URLs from eml file's content."""
        urls = set()
        with open(self.file_path) as eml:
            message = email.parser.Parser().parse(eml)

            for payload in message.get_payload():
                urls.update(self.handle_eml_payload(payload.get_payload()))

        return await self.process_list(urls)

    def handle_eml_payload(self, payload):
        """Decode and extract URLs from payload."""
        # payload is str, but quopri.decodestring expects bytes object
        decoded = quopri.decodestring(bytes(payload, 'utf-8'))
        pattern = re.compile(r'(https?://\S+?)[\"\'\>]')

        return pattern.findall(str(decoded))


def cli():
    """Parse command line arguments."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        'file_path',
        help='Specify optional file path with URLs to check.'
    )

    args = arg_parser.parse_args()

    checker = URLChecker(args.file_path)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(checker.handle_file())


if __name__ == '__main__':
    cli()
