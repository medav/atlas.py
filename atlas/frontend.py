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
    'StartCondition',
    'EndCondition',
    'RegisterOp',
    'otherwise'
]

circuit = None
modules = []
predicate = []
prevcondition = None

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
    global predicate
    return predicate

def Module(func):
    def ModuleWrapper(*args, **kwargs):
        global modules
        global predicate
        global prevcondition
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
            assert len(predicate) == 0
            prevcondition = None

            func(*args, **kwargs)

            assert len(modules) > 0
            m = modules.pop()

            assert len(predicate) == 0

            circuit.modules.append(m)

        return m

    return ModuleWrapper

def StartCondition(signal):
    global predicate
    predicate.append((signal, True))

def ElseCondition():
    global predicate
    global prevcondition
    assert prevcondition is not None
    predicate.append((prevcondition, False))

def EndCondition():
    global predicate
    global prevcondition
    assert len(predicate) > 0
    prevcondition = predicate.pop()[0]

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