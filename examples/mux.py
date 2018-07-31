import sys
sys.path.append('.')

from atlas import *

@Module
def Mux(n=8):
    io = Io({
        'a': Input(Bits(n)),
        'b': Input(Bits(n)),
        'sel': Input(Bits(1)),
        'foo': Input({
            'bazz': Bits(2),
            'buzz': [
                Bits(1) for _ in range(4)
            ]
        }),
        'out': Output(Bits(n))
    })

    with io.sel:
        io.out <<= io.b
    with otherwise:
        io.out <<= io.a

circuit = Circuit()
with circuit:
    top = Mux()

circuit.SetTop(top)

EmitCircuit(None, circuit)