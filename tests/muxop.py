import sys
sys.path.append('.')

from atlas import *

@Module
def MuxOp(mux_width, data_width):
    io = Io({
        'data_in': Input([Bits(data_width) for _ in range(mux_width)]),
        'index': Input(Bits(Log2Ceil(mux_width))),
        'data_out': Output(Bits(data_width))
    })

    io.data_out <<= Mux(io.data_in, io.index)

    NameSignals(locals())

circuit = Circuit('muxop')

with Context(circuit):
    circuit.top = MuxOp(8, 8)

EmitCircuit(circuit, 'tests/muxop.v')