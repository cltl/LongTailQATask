import pickle

class NewsItem:

    def __init__(self, title='',
                 content='',
                 dct='',
                 id=None,
                 uri=''):
        self.title = title
        self.content = content
        self.dct = dct
        self.id = id
        self.uri = uri

    def toJSON(self, targetFile):
        pickle.dump(self, open(targetFile, 'wb'))

