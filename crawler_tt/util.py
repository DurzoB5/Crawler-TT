from enum import Enum


SQL_ERRORS = [
    ('you have an error in your sql syntax;', 'MySQL injection detected'),
    ('warning: mysql', 'MySQL injection detected'),
    ('unclosed quotation mark after the character string', 'SQL injection detected'),
    ('quoted string not properly terminated', 'Oracle injection detected'),
]


class CrawlerMode(Enum):
    STANDALONE = 0
    SERVICE = 1
