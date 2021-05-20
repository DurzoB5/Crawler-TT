import logging
from typing import List
from urllib.parse import urlsplit

from crawler_tt.progress import ServiceProgressHandler, StandaloneProgressHandler
from crawler_tt.util import CrawlerMode

LOGGER = logging.getLogger('crawler')


class Crawler:
    """
    Main Crawler class that handles finding additional urls and checking any forms
    found on those urls for SQL injection vulnerabilities
    """

    def __init__(
        self,
        starting_url: str,
        payloads: List[str],
        mode: CrawlerMode,
        result: str,
        same_domain_only: bool,
        include_subdomains: bool,
        excluded_urls: List[str],
        log_level: str,
    ):
        """
        Create a crawler to crawl starting at the given starting url

        :param starting_url:  The url to start the crawl from
        :param payloads: A list of payloads to attempt
        :param mode: The mode the crawler should run in, this effects how results are
            stored
        :param result: If running in STANDALONE mode then this should be a path to
            either create the result file or of a result file from a previous
            incomplete run, if running in SERVICE mode this should be the ID of the
            database object to store results to
        :param same_domain_only: Flag whether to only test urls on the same domain as
            the starting url
        :param include_subdomains: Whether to include subdomains of the starting url
        :param excluded_urls: A list of urls to exclude from the crawl if seen
        :param log_level: The log level to run the crawler at
        """
        LOGGER.setLevel(log_level)

        LOGGER.debug(f'Creating Crawler to start at {starting_url}')

        self.starting_url = starting_url

        # Split the starting url and store the scheme and host for later
        split_url = urlsplit(starting_url)
        self.scheme = split_url.scheme
        self.host = split_url.netloc

        self.payloads = payloads
        self.same_domain_only = same_domain_only
        self.include_subdomains = include_subdomains
        self.excluded_urls = excluded_urls

        # Create the correct ProgressHandler based on the mode the crawler is running in
        self.progress = (
            StandaloneProgressHandler(result)
            if mode == CrawlerMode.STANDALONE
            else ServiceProgressHandler(result)
        )
