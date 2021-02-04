class BaseFile():
    def __init__(self, filename):
        self.filename = filename

    def active_mass(self):
        raise NotImplementedError()
