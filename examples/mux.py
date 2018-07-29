import sys
sys.path.append('.')

from atlas.frontend import *

@Module
def Mux(n):
    io = Io({
        'a': Input(Bits(n)),
        'b': Input(Bits(n)),
        'sel': Input(Bits(1)),
        'out': Output(Bits(n))
    })

    with io.sel:
        io.out <<= io.b
    with Otherwise():
        io.out <<= io.a

circuit = Circuit()
with circuit:
    top = Mux(8)

circuit.SetTop(top)
