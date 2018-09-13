import sys
sys.path.append('.')

from atlas import *

paddr_width = 64
ras_size = 8
ras_index_width = 3

@Module
def ReturnAddressStack():
    io = Io({
        'push': Input({
            'valid': Bits(1),
            'address': Bits(paddr_width)
        }),
        'pop': Output({
            'valid': Flip(Bits(1)),
            'address': Bits(paddr_width)
        })
    })

    rstack = Mem(paddr_width, ras_size)

    #
    # The return address stack is implemented as a circular buffer so values
    # don't need to be shifted around wasting energy.
    #

    enq_address = Reg(Bits(ras_index_width), reset_value=0)
    head = Wire(Bits(ras_index_width))

    head <<= enq_address - 1

    with io.push.valid & ~io.pop.valid:
        enq_address <<= enq_address + 1

    with io.pop.valid & ~io.push.valid:
        enq_address <<= enq_address - 1

    rstack.Write(enq_address, io.push.address, io.push.valid)
    io.pop.address <<= rstack.Read(head)

    NameSignals(locals())

@Module
def IFetchDummy():
    io = Io({
        'ras_push': Input(Bits(1)),
        'push_addr': Input(Bits(paddr_width)),
        'ras_pop': Input(Bits(1)),
        'pop_addr': Output(Bits(paddr_width))
    })

    ras = Instance(ReturnAddressStack())

    ras.push.valid <<= io.ras_push
    ras.push.address <<= io.push_addr

    ras.pop.valid <<= io.ras_pop
    io.pop_addr <<= ras.pop.address

    NameSignals(locals())


circuit = Circuit('portdir', True, True)

with Context(circuit):
    circuit.top = IFetchDummy()

EmitCircuit(circuit, 'tests/portdir.v')