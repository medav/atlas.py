import atlas.firrtl.emitter as emitter
from atlas.frontend.circuit import *
from atlas.frontend.module import *
from atlas.frontend.signal import *

circuit = Circuit('top')

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

        io.out.Assign(io.a)

        with io.sel:
            io.out.Assign(io.b)

mux = Mux('mymux')
circuit.ElaborateModule(mux)
emitter.EmitFirrtl('mux.fir', circuit)