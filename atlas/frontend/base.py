from .. import model
from contextlib import contextmanager

__all__ = ['Module', 'Circuit', 'CurrentModule', 'CurrentContext', 'StartCondition', 'EndCondition']

circuit = None
modules = []
context = []

class Circuit(model.Circuit):
    def __init__(self, _name):
        model.Circuit.__init__(self, _name)

    def __enter__(self):
        global circuit
        assert circuit is None
        circuit = self
        return self

    def __exit__(self, *kwargs):
        global circuit
        assert circuit == self
        circuit = None

def CurrentModule():
    global modules
    assert len(modules) > 0
    return modules[-1]

def CurrentContext():
    global context
    assert len(context) > 0
    return context[-1]

def Module(func):
    def ModuleWrapper(*kwargs):
        global modules
        global context
        global circuit

        modules.append(model.Module(func.__name__))
        context.append(CurrentModule())

        func(*kwargs)

        assert len(modules) > 0
        m = modules.pop()
        circuit.AddModule(m)

    return ModuleWrapper

def ContainsSignal(signal):
    while signal.parent is not None and type(signal.parent) is not model.Module:
        signal = signal.parent

    return signal.parent == CurrentModule()

def StartCondition(signal):
    global context
    condition = model.Condition(signal)
    CurrentContext().AddStmt(condition)
    context.append(condition)
    return condition

def EndCondition(condition):
    global context
    assert CurrentContext() == condition
    context.pop()