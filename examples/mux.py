import sys
sys.path.append('.')

from atlas import *

@Module
def Mux(n=8):
    io = Io({
        'a': Input(Bits(n)),
        'b': Input(Bits(n)),
        'sel': Input(Bits(1)),
        'out': Output(Bits(n))
    })

    with io.sel:
        io.out <<= io.b
    with otherwise:
        io.out <<= io.a

    NameSignals(locals())

circuit = Circuit('mux')

with Context(circuit):
    top = Mux()
    circuit.top = Mux()

EmitCircuit(circuit, 'test/mux.v')