from .. import model
from contextlib import contextmanager
import copy
from hashlib import sha256
from .. import op

__all__ = [
    'Module',
    'Circuit',
    'CurrentModule',
    'CurrentPredicate',
    'PreviousCondition',
    'StartCondition',
    'EndCondition',
    'Instance',
    'RegisterOp'
]

circuit = None
modules = []
predicate = None
prevcondition = None

class Circuit(model.Circuit):
    def __init__(self):
        model.Circuit.__init__(self, 'top')

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

def CurrentModule():
    global modules
    assert len(modules) > 0
    return modules[-1]

def CurrentPredicate():
    global predicate
    return predicate

def PreviousCondition():
    global prevcondition
    return prevcondition

def Module(func):
    def ModuleWrapper(*args, **kwargs):
        global modules
        global predicate
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
            assert predicate is None
            predicate = []
            prevcondition = None

            func(*args, **kwargs)

            assert len(modules) > 0
            m = modules.pop()
            predicate = None

            circuit.modules.append(m)

        return m

    return ModuleWrapper

instance_id_table = { }

def NewInstanceName(module_name):
    global instance_id_table

    if module_name in instance_id_table:
        instance_id_table[module_name] += 1
        id = instance_id_table[module_name]
    else:
        instance_id_table[module_name] = 0
        id = 0

    return f'{module_name}_inst_{id}'

def Instance(module):
    assert len(modules) > 0
    inst_name = NewInstanceName(module.name)
    inst = model.Instance(copy.deepcopy(module.io), inst_name, module.name)
    CurrentModule().AddInstance(inst)
    return inst

def StartCondition(signal):
    global predicate
    assert predicate is not None
    predicate.append(signal)

def EndCondition(signal):
    global predicate
    global prevcondition
    assert predicate is not None
    assert predicate[-1] is signal
    prevcondition = predicate[-1]
    predicate.pop()

def RegisterOp(aop):
    CurrentModule().ops.append(aop)
    return aop