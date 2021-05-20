import argparse
import os
from typing import List, Optional

import coloredlogs

from crawler_tt.crawler import Crawler


def run(
    url: str,
    payloads: List[str],
    result_file: str = 'crawl_results.json',
    same_domain_only: bool = True,
    include_subdomains: bool = True,
    excluded_urls: Optional[List[str]] = None,
    log_level: str = 'INFO',
    **kwargs,
) -> Crawler:
    """
    Function that creates and runs the crawler.

    Is either called by the `cli` function when running from the command line or
    directly from other services

    :param url: The url to start the crawl from
    :param payloads: The SQL injection payloads to try
    :param result_file: A path to either create the results file or of an existing
        incomplete results file
    :param same_domain_only: Flag whether to only test urls on the same domain as the
        starting url
    :param include_subdomains: Whether to include subdomains of the starting url
    :param excluded_urls: A list of urls to exclude from the crawl if seen
    :param log_level: The log level to run the crawler at
    """
    # Create the Crawler with the provided settings
    crawler = Crawler(
        url,
        payloads,
        result_file,
        same_domain_only,
        include_subdomains,
        excluded_urls if excluded_urls else [],
        log_level,
    )

    return crawler


def cli() -> None:
    """
    Function called when running the crawler from the CLI

    Handles retrieving CLI args before calling the crawler
    """
    parser = argparse.ArgumentParser(
        description='Crawler that crawls starting at the given URL searching for SQL '
        'injections in forms'
    )

    parser.add_argument('url', type=str, help='The url to start the crawl from')
    parser.add_argument(
        '-r',
        '--result-file',
        type=str,
        help='Either the output path to place the result file or a path to a '
        'previously incomplete result file',
    )
    parser.add_argument(
        '-p',
        '--payloads',
        type=open,
        help='A file containing custom payloads to use instead of the builtin ones. '
        'Each payload should be on it\'s own line',
        default=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'default_payload.txt'
        ),
    )
    parser.add_argument(
        '--include-all-domains',
        action='store_false',
        dest='same_domain_only',
        help='Whether to check for SQL injections against all domains found rather '
        'than just ones with the same domain as the starting url',
    )
    parser.add_argument(
        '--include-subdomains',
        action='store_true',
        help='Whether to check for SQL injections against subdomains of the domain '
        'provided in the starting url. (This has no effect if `--include-all-domains` '
        'provided',
    )
    parser.add_argument(
        '--excluded-urls',
        nargs='+',
        help='A list of urls that should be excluded from the crawl if they are seen',
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='The log level to set on the crawler',
    )

    args = parser.parse_args()

    coloredlogs.install(
        level=args.log_level, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # Read in the payload file and override the args namespace with the list of payloads
    args.payloads = [line.strip() for line in args.payloads.readlines()]

    run(**args.__dict__)


if __name__ == '__main__':
    cli()
