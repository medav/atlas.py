from .. import model
from contextlib import contextmanager
import copy
from hashlib import sha256

__all__ = [
    'Module',
    'Circuit',
    'CurrentModule',
    'CurrentContext',
    'StartCondition',
    'EndCondition',
    'Instance',
    'otherwise'
]

circuit = None
modules = []
context = []

class Circuit(model.Circuit):
    def __init__(self, _name='circuit'):
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
    def ModuleWrapper(*args, **kwargs):
        global modules
        global context
        global circuit

        print(f)

        if len(name) > 0:
            module_name = name
        else:
            uid = sha256(f'{args}, {kwargs}'.encode('utf-8')).hexdigest()[0:4]
            module_name = func.__name__ + '_' + uid

        m = None

        for module in circuit.modules:
            if module.name == module_name:
                m = module

        if m is None:
            modules.append(model.Module(module_name))
            context.append(CurrentModule())

            func(*args, **kwargs)

            assert len(modules) > 0
            m = modules.pop()
            context.pop()

            circuit.AddModule(m)

        return m

    return ModuleWrapper

instance_id_table = { }

def NewInstanceName(module_name):
    global instance_id_table

    if module_name in instance_id_table:
        instance_id_table[module_name] += 1
        id = instance_id_table[module_name]
        return f'{module_name}_inst_{id}'

    else:
        instance_id_table[module_name] = 0
        return f'{module_name}_inst_0'

def Instance(module):
    assert len(modules) > 0
    inst_name = NewInstanceName(module.name)
    inst = model.Instance(copy.deepcopy(module.io), inst_name, module.name)
    CurrentModule().AddInstance(inst)
    return inst

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

class ElseCondition():
    def __init__(self):
        pass

    def __enter__(self):
        assert type(CurrentContext().stmts[-1]) is model.Condition
        context.append(CurrentContext().stmts[-1].else_group)

    def __exit__(self, *kwargs):
        context.pop()

otherwise = ElseCondition()