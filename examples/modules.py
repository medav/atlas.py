import sys
sys.path.append('.')

import atlas.firrtl.emitter as emitter
from atlas.frontend import *

@Module
def FullAdder():
    io = Io({
        'cin': Input(Bits(1)),
        'a': Input(Bits(1)),
        'b': Input(Bits(1)),
        'sum_out': Output(Bits(1)),
        'cout': Output(Bits(1))
    })

    a_xor_b = io.a ^ io.b
    io.sum_out <<= a_xor_b ^ io.cin
    io.cout <<= (io.a & io.b) | (a_xor_b & io.cin)
    
    NameSignals(locals())

@Module('RippleAdder')
def RippleAdder(n):
    io = Io({
        'a': Input(Bits(n)),
        'b': Input(Bits(n)),
        'cin': Input(Bits(1)),
        'sum_out': Output(Bits(n)),
        'cout': Output(Bits(1))
    })

    carry = Wire(Bits(1, (n + 1,)))
    out_arr = Wire(Bits(1, (n,)))
    
    carry[0] <<= io.cin

    for i in range(n):
        fa = Instance(FullAdder())
        fa.io.cin <<= carry[i]
        fa.io.a <<= io.a(i, i)
        fa.io.b <<= io.b(i, i)
        carry[i + 1] <<= fa.io.cout
        out_arr[i] <<= fa.io.sum_out
    
    io.cout <<= carry[n]
    io.sum_out <<= Cat([out_arr[n - i - 1] for i in range(n)])

    NameSignals(locals())

circuit = Circuit('RippleAdder')
with circuit:
    RippleAdder(2)

emitter.EmitFirrtl('ripple-adder.fir', circuit)