import sys
sys.path.append('.')

from atlas import *

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

@Module
def RippleAdder(n):
    io = Io({
        'a': Input(Bits(n)),
        'b': Input(Bits(n)),
        'cin': Input(Bits(1)),
        'sum_out': Output(Bits(n)),
        'cout': Output(Bits(1))
    })

    carry = Wire([Bits(1) for i in range(n + 1)])
    out_arr = Wire([Bits(1) for i in range(n)])

    carry[0] <<= io.cin

    for i in range(n):
        fa = Instance(FullAdder())
        fa.cin <<= carry[i]
        fa.a <<= io.a(i, i)
        fa.b <<= io.b(i, i)
        carry[i + 1] <<= fa.cout
        out_arr[i] <<= fa.sum_out

    io.cout <<= carry[n]
    io.sum_out <<= Cat([out_arr[n - i - 1] for i in range(n)])

    NameSignals(locals())

circuit = Circuit()
with circuit:
    top = RippleAdder(8)

circuit.SetTop(top)

EmitCircuit(circuit, 'test/modules.v')