from ..model import *

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
        raise RuntimeError('Unknown type: {}'.format(type(item)))

def SignalTypeToString(signal):
    if issubclass(type(signal), Bits):
        base_type = "UInt"
        if signal.signed:
            base_type = "SInt"
        
        if signal.length == 1:
            return '{}<{}>'.format(base_type, signal.width)
        else:
            return '{}<{}>[{}]'.format(base_type, signal.width, signal.length)

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

signal_type_name = {
    Signal.WIRE: 'wire',
    Signal.REG: 'reg',
}

def EmitSignal(fw, signal):
    fw.WriteLine(
        '{} {}: {}'.format(
            signal_type_name[signal.sigtype], 
            signal.name,
            SignalTypeToString(signal)))

signal_dir_name = {
    Signal.INPUT: 'input',
    Signal.OUTPUT: 'output',
}

def EmitIo(fw, module):
    fw.WriteLine('output io: {}'.format(SignalTypeToString(module.io)))

def EmitNode(fw, node):
    fw.WriteLine('node')

def EmitAssignment(fw, assignment):
    lname = NameOf(assignment.lhs)
    rname = NameOf(assignment.rhs)
    fw.WriteLine('{} <= {}'.format(lname, rname))

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
            stmt_emit_map[type(stmt)](fw, stmt)

def EmitModule(fw, module):
    with Context(fw, 'module', module.name):
        EmitIo(fw, module)
        EmitStmts(fw, module)

def EmitFirrtl(filename, circuit):
    fw = FileWriter(open(filename, 'w'))

    with Context(fw, 'circuit', circuit.name):
        for module in circuit.modules:
            EmitModule(fw, module)