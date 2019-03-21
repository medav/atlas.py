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


def HwGcd(tb, a, b):
    tb.Reset(10)
    tb.io.in_a <<= a
    tb.io.in_b <<= b
    tb.io.start <<= 1
    tb.Step(1)
    tb.io.start <<= 0

    while tb.io.done.GetValue() == 0:
        tb.Step(1)

    return tb.io.out.GetValue()

def SwGcd(a, b):
    while b != 0:
        a, b = b, a % b

    return a

with TestModule(lambda: Gcd(64)) as tb:
    for i in range(2, 100):
        for j in range(2, 100):
            s = SwGcd(i, j)
            h = HwGcd(tb, i, j)
            if s >= 10:
                print(s, '==', h)
            assert s == h, f'Mismatch for Gcd({i}, {j})!'