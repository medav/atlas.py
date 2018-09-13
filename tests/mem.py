import sys
sys.path.append('.')

from atlas import *

@Module
def MemModule():
    io = Io({
        'raddr': Input(Bits(8)),
        'waddr': Input(Bits(8)),
        'wdata': Input(Bits(8)),
        'wen': Input(Bits(1)),
        'rdata': Output(Bits(8))
    })

    mem = Mem(8, 256)

    io.rdata <<= mem.Read(io.raddr)
    mem.Write(io.waddr, io.wdata, io.wen)

    NameSignals(locals())

circuit = Circuit('memmodule', True, True)

with Context(circuit):
    circuit.top = MemModule()

EmitCircuit(circuit, 'tests/memmodule.v')