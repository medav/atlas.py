from .. import model

class Module(model.Module):
    def __init__(self, _name):
        model.Module.__init__(self, _name)

    def PreElaborate(self):
        self.io.parent = self

    def Assign(self, signal, child):
        print('{} <= {}'.format(child, signal))

    def Elaborate():
        raise NotImplementedError()