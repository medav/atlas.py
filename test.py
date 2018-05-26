import atlas.firrtl.emitter as emitter
from atlas.frontend import *

@Module
def Mux(n):
    io = Io({
        'a': Input(Bits(n)),
        'b': Input(Bits(n)),
        'sel': Input(Bits(1)),
        'out': Output(Bits(n))
    })

    io.out.Assign(io.a)
    with io.sel:
        io.out.Assign(io.b)

circuit = Circuit('mymux')
with circuit:
    Mux(8)

emitter.EmitFirrtl('mux.fir', circuit)