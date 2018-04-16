import re

class Circuit(object):
    def __init__(self, _name):
        self.name = _name
        self.modules = []

    def AddModule(self, module):
        self.modules.append(module)

    def Regex():
        raise NotImplementedError()

    def __str__(self):
        return 'circuit {}'.format(self.name)

class Dtype(object):
    def __init__(self, _dtype_str):
        self.dtype_str = _dtype_str

class Module(object):
    def __init__(self, _name):
        self.name = _name
        self.inputs = {}
        self.outputs = {}
        self.regs = {}
        self.wires = {}
        self.nodes = {}
        self.insts = {}
        self.exprs = []

    def AddInput(self, input):
        self.inputs[input.name] = input

    def AddOutput(self, output):
        self.inputs[output.name] = output

    def AddReg(self, reg):
        self.regs[reg.name] = reg

    def AddWire(self, wire):
        self.wires[wire.name] = wire

    def AddSignal(self, signal):
        if signal.sigtype == 'input':
            self.AddInput(signal)
        elif signal.sigtype == 'output':
            self.AddOutput(signal)
        elif signal.sigtype == 'wire':
            self.AddWire(signal)
        elif signal.sigtype == 'reg':
            self.AddReg(signal)
        else:
            raise NotImplementedError()

    def AddNode(self, node):
        self.nodes[node.name] = node

    def AddInst(self, inst):
        self.insts[inst.name] = inst

    def AddExpr(self, expr):
        self.exprs.append(expr)

    def Regex():
        raise NotImplementedError()

    def __str__(self):
        return 'module {}'.format(self.name)

class Expr(object):
    def __init__(self):
        pass

class Signal(object):
    def __init__(self, _sigtype, _name, _dtype, _info):
        self.sigtype = _sigtype
        self.name = _name
        self.dtype = _dtype
        self.info = _info

    def FromString(line):
        regex = re.compile('(wire|reg|input|output) ([a-zA-Z_0-9]+)\\W*:\\W*(.*)(@\\[.*\\])?')
        m = regex.match(line.strip())
        sigtype = m.groups('')[0].strip()
        name = m.groups('')[1].strip()
        dtype = m.groups('')[2].strip()
        info = m.groups('')[3].strip()
        return Signal(sigtype, name, dtype, info)

class Node(object):
    def __init__(self, _name, _expr, _info):
        self.name = _name
        self.expr = _expr
        self.info = _info

    def FromString(line):
        regex = re.compile('node ([a-zA-Z_0-9]+)\\W*=\\W*(.*)(@\\[.*\\])?')
        m = regex.match(line.strip())
        name = m.groups('')[0].strip()
        expr = m.groups('')[1].strip()
        info = m.groups('')[2].strip()
        return Node(name, expr, info)

class Condition(Expr):
    def __init__(self, _condition_str):
        self.condition_str = _condition_str
        self.exprs = []
        self.wires = {}
        self.nodes = {}

    def AddExpr(self, expr):
        self.exprs.append(expr)

    def AddWire(self, wire):
        self.wires[wire.name] = wire

    def AddSignal(self, signal):
        if signal.sigtype == 'wire':
            self.AddWire(signal)
        else:
            raise NotImplementedError()

    def AddNode(self, node):
        self.nodes[node.name] = node

    def __str__(self):
        return 'when'

class PrimOp(Expr):
    def __init__(self, _opname, _args):
        self.opname = _opname
        self.args = _args

class Assignment(Expr):
    def __init__(self, _lhs, _rhs):
        self.lhs = _lhs
        self.rhs = _rhs

def ParseCircuit(context, line):
    if not line.startswith('circuit'):
        raise RuntimeError('Expected keyword: circuit')

    name = line.replace(':', '').strip().split(' ')[1]
    circuit = Circuit(name)
    context.append(circuit)

def ParseModule(context, line):
    if not line.strip().startswith('module'):
        raise RuntimeError('Expected keyword: module')

    name = line.replace(':', ' ').strip().split(' ')[1]
    module = Module(name)
    context[-1].AddModule(module)
    context.append(module)

def ParseSignal(context, line):
    context[-1].AddSignal(Signal.FromString(line))
    pass

def ParseNode(context, line):
    context[-1].AddNode(Node.FromString(line))
    pass

def ParseSkip(context, line):
    pass

def ParseWhen(context, line):
    condition_str = line.strip().replace(':', ' ').split(' ')[1]
    cond = Condition(condition_str)
    context[-1].AddExpr(cond)
    context.append(cond)

def ParseElse(context, line):
    condition_str = 'else'
    assert type(context[-1].exprs[-1]) is Condition
    cond_else = Condition('else')
    context[-1].exprs[-1].cond_else = cond_else
    context.append(cond_else)

parse_vector = {
    'input': ParseSignal,
    'output': ParseSignal,
    'reg': ParseSignal,
    'wire': ParseSignal,
    'node': ParseNode,
    'skip': ParseSkip,
    'when': ParseWhen,
    'else': ParseElse
}

def ParseStatement(context, line):
    line_stripped = line.strip()
    for key in parse_vector:
        if line_stripped.startswith(key):
            parse_vector[key](context, line)
            return
    
    context[-1].AddExpr(line.strip())

def ParseFirrtl(f):
    indent_level = 0
    prev_indent_level = 0
    indent_spaces = 0
    context = []
    line_num = 0

    try:
        for line in f:
            line_num += 1
            if len(line.strip()) == 0 or line.strip().startswith(';'):
                continue

            if line.startswith(' '):
                if indent_spaces == 0:
                    indent_spaces = len(line) - len(line.lstrip())

                indent_level = int((len(line) - len(line.lstrip())) / indent_spaces)
            else:
                indent_level = 0

            if indent_level < prev_indent_level:
                for i in range(prev_indent_level - indent_level):
                    context.pop()

            if indent_level == 0:
                ParseCircuit(context, line)
            elif indent_level == 1:
                ParseModule(context, line)
            else:
                ParseStatement(context, line)

            prev_indent_level = indent_level

    except Exception as e:
        print('Exception at line {}'.format(line_num))
        print('line = \"{}\"'.format(line.rstrip()))
        print('indent_level = {}'.format(indent_level))
        print('prev_indent_level = {}'.format(prev_indent_level))
        print([c.__str__() for c in context])
        raise

    return context[0]