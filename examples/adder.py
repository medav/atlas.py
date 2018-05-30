import atlas.firrtl.emitter as emitter
from atlas.frontend import *

def FullAdder(cin, a, b):
    a_xor_b = a ^ b
    sum_out = a_xor_b ^ cin
    cout = (a & b) | (a_xor_b & cin)
    return sum_out, cout

def RippleAdderIo(n):
    return {
        'a': Input(Bits(n)),
        'b': Input(Bits(n)),
        'cin': Input(Bits(1)),
        'sum_out': Output(Bits(n)),
        'cout': Output(Bits(1))
    }

@Module
def RippleAdder(n):
    io = Io(RippleAdderIo(n))

    carry = io.cin
    out_arr = Wire(Bits(1, (n,)))

    for i in range(n):
        sum_i, carry = FullAdder(carry, io.a(i, i), io.b(i, i))
        out_arr[i] <<= sum_i
    
    io.cout <<= carry
    io.sum_out <<= Cat([out_arr[n - i - 1] for i in range(n)])

    NameSignals(locals())

circuit = Circuit('RippleAdder')
with circuit:
    RippleAdder(2)

emitter.EmitFirrtl('ripple-adder.fir', circuit)