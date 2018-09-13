import sys
sys.path.append('.')

from atlas import *

def FullAdder(cin, a, b):
    a_xor_b = a ^ b
    sum_out = a_xor_b ^ cin
    cout = (a & b) | (a_xor_b & cin)
    return sum_out, cout

@Module
def RippleAdder(n):
    io = Io({
        'a': Input(Bits(n)),
        'b': Input(Bits(n)),
        'cin': Input(Bits(1)),
        'sum_out': Output(Bits(n)),
        'cout': Output(Bits(1))
    })

    carry = io.cin
    out_arr = Wire([Bits(1) for i in range(n)])

    for i in range(n):
        sum_i, carry = FullAdder(carry, io.a(i, i), io.b(i, i))
        out_arr[i] <<= sum_i

    io.cout <<= carry
    io.sum_out <<= Cat([out_arr[n - i - 1] for i in range(n)])

    NameSignals(locals())

circuit = Circuit('adder')

with Context(circuit):
    top = RippleAdder(4)

circuit.top = top

EmitCircuit(circuit, 'tests/adder.v')