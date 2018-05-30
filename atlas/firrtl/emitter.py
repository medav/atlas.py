from ..model import *
from .shared import *

indent_str = '  '

class FileWriter(object):
    def __init__(self, _f):
        self.f = _f
        self.indent = 0

    def WriteLine(self, line):
        self.f.write(indent_str * self.indent + line + '\n')

    def WriteLines(self, line):
        for line in lines:
            self.WriteLine(line)

    def Indent(self):
        self.indent += 1

    def Dedent(self):
        self.indent -= 1

class Context(object):
    def __init__(self, _fw, _prefix, _name, _info=''):
        self.fw = _fw
        self.prefix = _prefix
        self.name = _name
        self.info = _info

    def __enter__(self):
        self.fw.WriteLine(self.prefix + ' ' + self.name + ':' + self.info)
        self.fw.Indent()

    def __exit__(self, *args):
        self.fw.Dedent()

def SignalName(signal):
    name = signal.name

    if issubclass(type(signal), BitsElement):
        signal = signal.parent
        name = signal.name + name

    while signal.parent is not None and not issubclass(type(signal.parent), Module):
        name = signal.parent.name + '.' + name
        signal = signal.parent

    return name

def NodeName(node):
    return node.name

def NameOf(item):
    if issubclass(type(item), Node):
        return NodeName(item)
    elif issubclass(type(item), Signal):
        return SignalName(item)
    else:
        return str(item)

def SignalTypeToString(signal):
    if issubclass(type(signal), Bits):
        base_type = "UInt"
        if signal.signed:
            base_type = "SInt"
        
        if signal.shape == (1,):
            return '{}<{}>'.format(base_type, signal.elemwidth)
        else:
            return '{}<{}>[{}]'.format(base_type, signal.elemwidth, signal.shape[0])

    elif issubclass(type(signal), Bundle):
        return '{' + ', '.join([
            ('flip ' if s.sigdir == Signal.FLIP else '') +
            s.name +
            ': ' + 
            SignalTypeToString(s)
            for s in signal
        ]) + '}'
    
    else:
        raise NotImplementedError('Cannot serialize signal type: {}'.format(signal))

def EmitSignal(fw, signal):
    if signal.sigtype == Signal.WIRE:
        fw.WriteLine(f'{signal_type_str[signal.sigtype]} {signal.name}: {SignalTypeToString(signal)}')
    elif signal.sigtype == Signal.REG:
        fw.WriteLine(f'{signal_type_str[signal.sigtype]} {signal.name}: {SignalTypeToString(signal)}, clock')

def EmitIo(fw, module):
    if module.has_state:
        fw.WriteLine('input clock: Clock')
        fw.WriteLine('input reset: UInt<1>')

    fw.WriteLine('output io: {}'.format(SignalTypeToString(module.io)))

def EmitNode(fw, node):
    str_args = ', '.join([NameOf(arg) for arg in node.args])
    fw.WriteLine(f'node {node.name} = {node.primop}({str_args})')

def EmitAssignment(fw, assignment):
    lname = NameOf(assignment.lhs)
    rname = NameOf(assignment.rhs)
    fw.WriteLine(f'{lname} <= {rname}')

stmt_emit_map = {
    Signal: EmitSignal,
    Node: EmitNode,
    Assignment: EmitAssignment
}

def EmitStmts(fw, context):
    for stmt in context.stmts:
        if type(stmt) is Condition:
            with Context(fw, 'when', NameOf(stmt.condition)):
                EmitStmts(fw, stmt)
        else:
            for key in stmt_emit_map:
                if issubclass(type(stmt), key):
                    stmt_emit_map[key](fw, stmt)

def EmitModule(fw, module):
    with Context(fw, 'module', module.name):
        EmitIo(fw, module)
        EmitStmts(fw, module)

def EmitFirrtl(filename, circuit):
    fw = FileWriter(open(filename, 'w'))

    with Context(fw, 'circuit', circuit.name):
        for module in circuit.modules:
            EmitModule(fw, module)