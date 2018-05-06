from .backend import *
from .signals import *


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

def SignalTypeString(sigtype):
    return {
        Signal.INPUT: 'input',
        Signal.OUTPUT: 'output',
        Signal.WIRE: 'wire',
        Signal.REG: 'reg',
        Signal.NODE: 'node'
    }[sigtype]

def EmitSignal(fw, sig):
    fw.WriteLine('{} {}: {} {}'.format(SignalTypeString(sig.sigtype), sig.name, '', ''))

def EmitIo(fw, module):
    for signal in module.io:
        EmitSignal(fw, signal)

def EmitModule(fw, module):
    with Context(fw, 'module', module.name):
        EmitIo(fw, module)

def EmitFirrtl(filename, circuit):
    fw = FileWriter(open(filename, 'w'))

    with Context(fw, 'circuit', circuit.name):
        for module in circuit.modules:
            EmitModule(fw, module)