from contextlib import contextmanager
import copy
from hashlib import sha256

from . import model
from . import op

__all__ = [
    'Module',
    'Circuit',
    'CurrentModule',
    'CurrentContext',
    'StartCondition',
    'EndCondition',
    'Instance',
    'RegisterOp',
    'otherwise'
]

circuit = None
modules = []
context = []

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

def CurrentContext():
    global context
    assert len(context) > 0
    return context[-1]

def Module(func):
    def ModuleWrapper(*args, **kwargs):
        global modules
        global context
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
            assert len(context) == 0
            context.append(CurrentModule().connections)
            prevcondition = None

            func(*args, **kwargs)

            assert len(modules) > 0
            m = modules.pop()

            assert len(context) == 1
            context.pop()

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
    global context
    block = model.ConnectionBlock(predicate=signal)
    CurrentContext().append(block)
    context.append(block.true_block)

def ElseCondition():
    global context
    block = CurrentContext()[-1]
    assert type(block) is model.ConnectionBlock
    context.append(block.false_block)

def EndCondition():
    global context
    context.pop()

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