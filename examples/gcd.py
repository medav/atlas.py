import sys
sys.path.append('.')

from atlas import *

@Module
def Gcd(data_width):
    io = Io({
        'in_a': Input(Bits(data_width)),
        'in_b': Input(Bits(data_width)),
        'start': Input(Bits(1)),
        'out': Output(Bits(data_width)),
        'done': Output(Bits(1))
    })

    a_reg = Reg(Bits(data_width))
    b_reg = Reg(Bits(data_width))

    with io.start:
        a_reg <<= io.in_a
        b_reg <<= io.in_b

    with otherwise:
        with a_reg > b_reg:
            a_reg <<= a_reg - b_reg

        with otherwise:
            b_reg <<= b_reg - a_reg

    io.done <<= (b_reg == 0)
    io.out <<= a_reg

    NameSignals(locals())

circuit = Circuit(True, True)
with circuit:
    top = Gcd(64)

circuit.SetTop(top)

EmitCircuit(circuit, 'test/gcd.v')