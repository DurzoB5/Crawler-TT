from uuid import UUID


class Crawl:
    def __init__(self, id: UUID):
        self.id = id


def get_crawl(id: UUID) -> Crawl:
    return Crawl(id)
