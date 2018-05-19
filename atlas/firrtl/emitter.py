from ..model import *

class FileWriter(object):
    def __init__(self, _f):
        self.f = _f
        self.indent = 0

    def WriteLine(self, line):
        self.f.write('    ' * self.indent + line + '\n')

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
        self.fw.WriteLine(self.prefix + ' ' + self.name + ' : ' + self.info)
        self.fw.Indent()

    def __exit__(self, *args):
        self.fw.Dedent()

signal_type_name = {
    Signal.WIRE: 'wire',
    Signal.REG: 'reg',
}

def SignalName(signal):
    name = signal.name

    while signal.parent is not None and not issubclass(type(signal.parent), Module):
        name = signal.parent.name + '.' + name
        signal = signal.parent

    return name

def EmitSignal(fw, signal):
    fw.WriteLine('{} {}: {} {}'.format(signal_type_name[signal.sigtype], signal.name, '', ''))

def EmitNode(fw, node):
    fw.WriteLine('node')

def EmitAssignment(fw, assignment):
    lname = SignalName(assignment.lhs)
    rname = SignalName(assignment.rhs)
    fw.WriteLine('{} <= {}'.format(lname, rname))

stmt_emit_map = {
    Signal: EmitSignal,
    Node: EmitNode,
    Assignment: EmitAssignment
}

def EmitStmts(fw, context):
    for stmt in context.stmts:
        if type(stmt) is Condition:
            with Context(fw, 'when', ''):
                EmitStmts(fw, stmt)
        else:
            stmt_emit_map[type(stmt)](fw, stmt)

signal_dir_name = {
    Signal.INPUT: 'input',
    Signal.OUTPUT: 'output',
}

def EmitIo(fw, module):
    for signal in module.io:
        fw.WriteLine('{} {}: {} {}'.format(signal_dir_name[signal.sigdir], signal.name, '', ''))

def EmitModule(fw, module):
    with Context(fw, 'module', module.name):
        EmitIo(fw, module)
        EmitStmts(fw, module)

def EmitFirrtl(filename, circuit):
    fw = FileWriter(open(filename, 'w'))

    with Context(fw, 'circuit', circuit.name):
        for module in circuit.modules:
            EmitModule(fw, module)