import sys
sys.path.append('.')

from atlas import *

@Module
def MyMux(n=8):
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

circuit = Circuit('mymux')

with Context(circuit):
    circuit.top = MyMux()

EmitCircuit(circuit, 'tests/mymux.v')