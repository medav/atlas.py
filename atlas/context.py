from contextlib import contextmanager
import copy
from hashlib import sha256

from .debug import *
from .utilities import *

from . import model

__all__ = [
    'Module',
    'Circuit',
    'CurrentCircuit',
    'CurrentModule',
    'CurrentPredicate',
    'PrevCondition',
    'ConnectionContext',
    'StartCondition',
    'EndCondition',
    'RegisterOp',
    'otherwise'
]

circuit = None
modules = []
context = []
prevcondition = []

class Circuit(model.Circuit):
    def __init__(self, clock=False, reset=False):
        config = model.CircuitConfig(clock, reset)
        model.Circuit.__init__(self, 'top', config=config)

    def SetTop(self, module):
        assert module in self.modules
        self.top = module

    def __enter__(self):
        global circuit
        assert circuit is None
        circuit = self
        return self

    def __exit__(self, *kwargs):
        global circuit
        assert circuit == self
        circuit = None

def CurrentCircuit():
    global circuit
    return circuit

def CurrentModule():
    global modules
    assert len(modules) > 0
    return modules[-1]

def CurrentPredicate():
    global context
    assert len(context) > 0
    return context[-1]

def PrevCondition():
    global prevcondition
    assert prevcondition[-1] is not None
    return prevcondition[-1]

def SetPrevCondition(signal):
    global prevcondition
    assert len(prevcondition) > 0
    prevcondition[-1] = signal

def PushNewContext():
    global context
    global prevcondition
    assert len(context) == len(prevcondition)
    context.append([])
    prevcondition.append(None)

def PopContext():
    global context
    global prevcondition
    assert len(context) == len(prevcondition)
    assert len(context) > 0
    context.pop()
    prevcondition.pop()

@contextmanager
def ConnectionContext():
    PushNewContext()
    yield
    assert len(CurrentPredicate()) == 0
    PopContext()

def Module(func):
    def ModuleWrapper(*args, **kwargs):
        global modules
        global circuit

        module_name = func.__name__

        if (args != ()) or (kwargs != {}):
            uid = sha256(f'{args}, {kwargs}'.encode('utf-8')).hexdigest()[0:4]
            module_name = func.__name__ + '_' + uid

        m = None

        for module in circuit.modules:
            if module.name == module_name:
                m = module

        if m is None:
            modules.append(model.Module(module_name))

            with ConnectionContext():
                func(*args, **kwargs)

            assert len(modules) > 0
            m = modules.pop()
            circuit.modules.append(m)

        return m

    return ModuleWrapper

def StartCondition(signal):
    CurrentPredicate().append((signal, True))

def ElseCondition():
    CurrentPredicate().append((PrevCondition(), False))

def EndCondition():
    assert len(CurrentPredicate()) > 0
    SetPrevCondition(CurrentPredicate().pop()[0])

class OtherwiseObject(object):
    def __init__(self):
        pass

    def __enter__(self):
        ElseCondition()

    def __exit__(self, *args):
        EndCondition()

otherwise = OtherwiseObject()

def RegisterOp(aop):
    CurrentModule().ops.append(aop)
    return aop