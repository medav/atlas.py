from .model import *
from .verilog import *

__all__ = [
    'EmitModule',
    'EmitCircuit'
]

# @dataclass
# class Module(object):
#     name : str
#     io : dict = field(default=None, compare=False)
#     instances : dict = field(default_factory=lambda: {}, compare=False, repr=False)
#     signals : dict = field(default_factory=lambda: {}, compare=False, repr=False)
#     ops : list = field(default_factory=lambda: [], compare=False, repr=False)

def EmitModule(f, module):
    with VModule(f, module.name, module.io.io_dict):
        pass

def EmitCircuit(f, circuit):
    for module in circuit.modules:
        EmitModule(f, module)