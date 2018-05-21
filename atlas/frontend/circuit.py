from .. import model
from .module import *

__all__ = ['Circuit']

class Circuit(model.Circuit):
    def __init__(self, _name):
        model.Circuit.__init__(self, _name)

    def ElaborateModule(self, module):
        module.PreElaborate()
        module.Elaborate()
        self.AddModule(module)