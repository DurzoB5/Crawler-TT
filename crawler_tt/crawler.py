import logging
import re
from typing import List
from urllib.parse import SplitResult, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from crawler_tt.exceptions import InvalidResponseException
from crawler_tt.progress import (
    Result,
    ServiceProgressHandler,
    StandaloneProgressHandler,
    State,
)
from crawler_tt.util import SQL_ERRORS, CrawlerMode

LOGGER = logging.getLogger('crawler')


class Crawler:
    """
    Main Crawler class that handles finding additional urls and checking any forms
    found on those urls for SQL injection vulnerabilities
    """

    def _dvwa_login(self) -> None:
        """Function that authenticates with a DVWA instance"""
        login_payload = {'username': 'admin', 'password': 'password', 'Login': 'Login'}
        login_url = f'{self.scheme}://{self.host}/login.php'

        # Navigate to the login page to retrieve the user token
        response = self.session.get(login_url)
        token = re.search("user_token'\s*value='(.*?)'", response.text).group(1)
        login_payload['user_token'] = token

        # Post the credentials to the login page so we are authenticated
        self.session.post(login_url, data=login_payload)

    def _get_page(self, url: str) -> BeautifulSoup:
        """
        Retrieve the contents of a given URL and load it into a BeautifulSoup object

        :param url: The url to retrieve
        :raise InvalidResponseException: If the request to the URL returns a response
            code other than 200
        :return: The contents of the page as a BeautifulSoup object
        """
        LOGGER.debug(f'Retrieving page from {url}')
        try:
            response = self.session.get(url)

            if response.status_code != 200:
                raise InvalidResponseException(
                    f'{url} returned status code {response.status_code}'
                )

            return BeautifulSoup(response.content, features='html.parser')
        except requests.ConnectionError:
            raise InvalidResponseException(f'{url} could not be reached')

    def _build_url(self, parts: SplitResult) -> str:
        """
        Build a URL from a urlparse using the starting url to replace missing schemes
        /hosts

        Will strip off any URL parameters

        :param parts: A URL from a href that has been split
        :return: The full url
        """
        LOGGER.debug(f'Building url from {parts.scheme}, {parts.netloc}, {parts.path}')
        scheme = parts.scheme if parts.scheme else self.scheme
        host = parts.netloc if parts.netloc else self.host
        path = parts.path if parts.path.startswith('/') else f'/{parts.path}'
        path = path.replace('../', '')

        return f'{scheme}://{host}{path}'

    def _get_urls_from_page(self, page: BeautifulSoup) -> List[str]:
        LOGGER.debug('Looking for new urls')
        found_urls = []

        # Find all `a` html tags on the page
        link_tags = page.findAll('a', href=True)
        for link_tag in link_tags:
            if link := link_tag.get('href'):
                LOGGER.debug(f'Found href {link}')
                if link == '.':
                    LOGGER.debug(
                        f'Skipping {link} as it\'s the same as the current location'
                    )
                    continue

                link_parts = urlsplit(link)

                if not link_parts.path or link_parts.scheme not in [
                    '',
                    'http',
                    'https',
                ]:
                    LOGGER.debug(f'Skipping {link} as it has an unsupported scheme')
                    continue

                # If the crawler is only looking for urls with the same domain
                # and the netloc of the found url is not empty then the crawler
                # needs to check either the host matches or is a subdomain
                if self.same_domain_only and link_parts.netloc != '':
                    if self.include_subdomains:
                        if self.host not in link_parts.netloc:
                            LOGGER.debug(
                                f'Skipping {link} as it is not a subdomain of '
                                f'{self.host}'
                            )
                            continue
                    else:
                        if link_parts.netloc != self.host:
                            LOGGER.debug(
                                f'Skipping {link} as it is not the same domain as '
                                f'{self.host}'
                            )
                            continue

                # Build the new url making sure all query params are removed
                found_urls.append(self._build_url(link_parts))

        return found_urls

    def _test_forms_vulnerable(self, url: str, page: BeautifulSoup) -> None:
        for form in page.findAll('form'):
            error_found = False
            form_id = form.attrs.get('id', '')
            LOGGER.debug('Checking form with ID: {form_id}')
            for payload in self.payloads:
                data = {}
                form_url = urljoin(url, form.attrs.get('action', ''))
                method = form.attrs.get('method', 'get').lower()

                for input_field in form.findAll('input'):
                    if input_field.attrs.get('type') != 'submit':
                        data[
                            input_field.attrs.get('name')
                        ] = f'{input_field.attrs.get("value", "")}{payload}'
                    else:
                        data[input_field.attrs.get('name')] = input_field.attrs.get(
                            'value', ''
                        )

                if method != 'get':
                    response = getattr(self.session, method)(
                        form_url, data=data, headers={'security': 'low'}
                    )
                else:
                    response = self.session.get(
                        form_url, params=data, headers={'security': 'low'}
                    )

                for error in SQL_ERRORS:
                    if error[0] in response.content.decode('utf-8').lower():
                        LOGGER.warning(
                            f'SQL injection found at {url} on form {form_id}'
                        )
                        self.progress.store_result(
                            url,
                            Result(
                                State.VULNERABLE,
                                f'{error[1]} on form {form_id}',
                            ),
                        )
                        error_found = True

                if error_found:
                    # If an error has been found stop trying payloads
                    break

            if error_found:
                # If an error has been found stop trying payloads
                break
            else:
                # If no error has been found mark the url as safe
                LOGGER.debug(f'{url} has no errors, marking as safe')
                self.progress.store_result(
                    url, Result(State.SAFE, 'No injections found')
                )
        else:
            # If no forms are found then mark the url as safe
            LOGGER.debug(f'{url} has no forms, marking as safe')
            self.progress.store_result(url, Result(State.SAFE, 'No injections found'))

    def __init__(
        self,
        starting_url: str,
        payloads: List[str],
        mode: CrawlerMode,
        result: str,
        same_domain_only: bool,
        include_subdomains: bool,
        excluded_urls: List[str],
        testing_dvwa: bool,
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
        :param testing_dvwa: Whether the crawler is testing DVWA, if true additional
            actions will be performed such as logging in and sending the security
            header in requests
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
        self.testing_dvwa = testing_dvwa
        self.session = requests.Session()
        if testing_dvwa:
            # If testing DVWA then set the security cookie to low
            LOGGER.info('Setting security cookie')
            self.session.cookies.set('security', 'low')

        # Create the correct ProgressHandler based on the mode the crawler is running in
        LOGGER.debug(f'Creating progress handler for {mode}')
        self.progress = (
            StandaloneProgressHandler(result)
            if mode == CrawlerMode.STANDALONE
            else ServiceProgressHandler(result)
        )

    def start(self) -> None:
        """Function to start crawling from the starting url"""
        LOGGER.info('Starting crawler...')
        urls_to_test = [self.starting_url]

        # Loop while there are still urls to be tested
        while urls_to_test:
            # Get a url to test
            url = urls_to_test.pop()
            LOGGER.info(f'Testing {url}, {len(urls_to_test)} urls remaining')

            try:
                try:
                    if self.testing_dvwa:
                        self._dvwa_login()

                    page = self._get_page(url)
                except InvalidResponseException as e:
                    msg = f'Failed to process {url} because {e}'
                    LOGGER.warning(msg)
                    self.progress.store_result(url, Result(State.FAILURE, msg))
                    continue

                # Check if this URL has already been checked in a previous run
                if url not in self.progress.urls:
                    # Find any forms on the page that we can try to inject
                    self._test_forms_vulnerable(url, page)

                # Find any suitable links to other pages the crawler should test
                for url in self._get_urls_from_page(page):
                    if url not in urls_to_test and url not in self.progress.urls:
                        LOGGER.info(f'Found {url} to test')
                        urls_to_test.append(url)

            except Exception as e:
                msg = f'Failed to process {url} because {e}'
                LOGGER.error(msg)
                self.progress.store_result(url, Result(State.FAILURE, msg))
                continue
