class BaseProgressHandler:
    def __init__(self, result: str):
        raise NotImplementedError()


class StandaloneProgressHandler(BaseProgressHandler):
    pass


class ServiceProgressHandler(BaseProgressHandler):
    pass
