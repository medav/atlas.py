from .. import model
from .. import op
from .base import *
from .typespec import *

class BinaryOperator(op.AtlasOperator):
    def __init__(self, sig_a, sig_b, opname, verilog_op):
        assert issubclass(type(sig_a), model.BitsSignal)
        assert issubclass(type(sig_b), model.BitsSignal)
        assert sig_a.width == sig_b.width

        super().__init__(Bits(sig_a.width, False), opname)

        self.sig_a = sig_a
        self.sig_b = sig_b
        self.verilog_op = verilog_op

    def Synthesize(self):
        VAssign(
            VName(self.result),
            f'{VName(self.sig_a)} {self.verilog_op} {VName(self.sig_b)}')

class AddOperator(BinaryOperator):
    def __init__(self, sig_a, sig_b):
        super().__init__(sig_a, sig_b, 'add', '+')

def Add(sig_a, sig_b):
    return RegisterOp(AddOperator(sig_a, sig_b))

class SubOperator(BinaryOperator):
    def __init__(self, sig_a, sig_b):
        super().__init__(sig_a, sig_b, 'sub', '-')

def Sub(sig_a, sig_b):
    return RegisterOp(SubOperator(sig_a, sig_b))

class MulOperator(BinaryOperator):
    def __init__(self, sig_a, sig_b):
        super().__init__(sig_a, sig_b, 'mul', '*')

class DivOperator(BinaryOperator):
    def __init__(self, sig_a, sig_b):
        super().__init__(sig_a, sig_b, 'div', '/')

class LShfOperator(BinaryOperator):
    def __init__(self, sig_a, sig_b):
        super().__init__(sig_a, sig_b, 'lshf', '<<')

class RShfOperator(BinaryOperator):
    def __init__(self, sig_a, sig_b):
        super().__init__(sig_a, sig_b, 'rshf', '>>')

class NotOperator(op.AtlasOperator):
    def __init__(self, sig_a):
        assert issubclass(type(sig_a), model.BitsSignal)
        super().__init__(Bits(sig_a.width, False), 'not')
        self.sig_a = sig_a

    def Synthesize(self):
        VAssign(VName(self.result), f'!{VName(self.sig_a)}')

def Not(sig_a):
    return RegisterOp(NotOperator(sig_a))