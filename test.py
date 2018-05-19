import atlas.parser as parser
import atlas.emitter as emitter
from atlas.frontend.context import *
from atlas.frontend.elaborate import *
from atlas.signals import *

CreateDefaultCircuit('top')

class Mux(Module):
    def __init__(self, _name):
        Module.__init__(self, _name)
        self.io = Io({
            'a': Input(Bits(1)),
            'b': Input(Bits(1)),
            'sel': Input(Bits(1)),
            'out': Output(Bits(1))
        })

    def Elaborate(self):
        io = self.io

        with io.sel:
            io.out.Assign(io.b)

        with Else:
            io.out.Assign(io.a)

pt = Elaborate(Mux('mymux'))
emitter.EmitFirrtl('mux.fir', pt)