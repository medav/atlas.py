from contextlib import contextmanager
from hashlib import sha256

from ..base import *

circuit = None
modules = []
context = []
prevcondition = []
optable = []
temp_num = 0

def NewWireName():
    global temp_num
    name = f'wire{temp_num}'
    temp_num += 1
    return name

def NewRegName():
    global temp_num
    name = f'reg{temp_num}'
    temp_num += 1
    return name

def Circuit(name : str, default_clock=False, default_reset=False):
    return M.Circuit(name, M.CircuitConfig(default_clock, default_reset))

@contextmanager
def Context(_circuit : M.Circuit):
    global circuit
    assert circuit is None
    circuit = _circuit

    yield

    assert circuit == _circuit
    circuit = None

def CurrentCircuit():
    global circuit
    return circuit

def CurrentModule():
    global modules
    assert len(modules) > 0
    return modules[-1]

def DefaultClock():
    assert CurrentCircuit().config.default_clock
    return CurrentModule().io_dict['clock']

def DefaultReset():
    assert CurrentCircuit().config.default_reset
    return CurrentModule().io_dict['reset']

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

def CurrentOpTable():
    global optable
    assert len(optable) > 0
    return optable[-1]

def PushNewContext():
    global context
    global prevcondition
    global optable
    assert len(context) == len(prevcondition)
    context.append([])
    prevcondition.append(None)
    optable.append({})

def PopContext():
    global context
    global prevcondition
    assert len(context) == len(prevcondition)
    assert len(context) > 0
    context.pop()
    prevcondition.pop()
    optable.pop()

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

def OpGen(cacheable=False, default=None):
    def DefaultFilter(op):
        if default is None:
            return op
        else:
            return op.__getattribute__(default)

    def OpGenDecorator(func):
        def OpGenWrapper(*args, **kwargs):
            op = func(*args, **kwargs)

            if not cacheable:
                CurrentModule().ops.append(op)
                return DefaultFilter(op)

            optable = CurrentOpTable()
            op_hash = hash(op)

            if op_hash not in optable:
                optable[op_hash] = [op]
                CurrentModule().ops.append(op)
                return DefaultFilter(op)

            for other_op in optable[op_hash]:
                if other_op == op:
                    return DefaultFilter(other_op)

            optable[op_hash].append(op)
            CurrentModule().ops.append(op)
            return DefaultFilter(op)

        return OpGenWrapper
    return OpGenDecorator