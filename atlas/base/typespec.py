from dataclasses import *

from . import model as M

@dataclass
class TypeMeta(object):
    sigdir : int = M.SignalDir.INHERIT

@dataclass
class Bits(object):
    width : int
    signed : bool = False
    meta : TypeMeta = field(default_factory=TypeMeta)

@dataclass
class List(object):
    length : int
    field_type : any
    meta : TypeMeta = field(default_factory=TypeMeta)

@dataclass
class Bundle(object):
    fields : dict
    meta : TypeMeta = field(default_factory=TypeMeta)

def BuildTypespec(primitive_spec):
    if type(primitive_spec) is Bits:
        return primitive_spec
    elif type(primitive_spec) is list:
        return List(len(primitive_spec), BuildTypespec(primitive_spec[0]))
    elif type(primitive_spec) is dict:
        return Bundle({
                key:BuildTypespec(primitive_spec[key])
                for key in primitive_spec
            })
    elif type(primitive_spec) is List:
        return primitive_spec
    elif type(primitive_spec) is Bundle:
        return primitive_spec
    else:
        assert False, f"Cannot build typespec from {primitive_spec}"

def CompareTypespec(type1, type2):
    if type(type1) != type(type2):
        return False

    if type(type1) is list:
        if len(type1) != len(type2):
            return False

        return reduce(
            lambda x, y: x and y,
            map(
                lambda x: CompareTypespec(x[0], x[1]),
                zip(type1, type2)))

    else:
        if set(type1.keys()) != set(type2.keys()):
            return False

        return reduce(
            lambda x, y: x and y,
            map(
                lambda x: CompareTypespec(x[0], x[1]),
                ((type1[key], type2[key]) for key in type1)))

def TypespecOf(signal):
    """Reproduce a typespec for a given signal."""

    if type(signal) is M.BitsSignal:
        return Bits(signal.width, signal.signed, TypeMeta(signal.meta.sigdir))

    elif type(signal) is M.ListSignal:
        return List(
            len(signal.fields),
            TypespecOf(signal.fields[0]),
            TypeMeta(signal.meta.sigdir))

    elif type(signal) is M.BundleSignal:
        return Bundle(
            { key: TypespecOf(signal.fields[key]) for key in signal.fields },
            TypeMeta(signal.meta.sigdir))

    else:
        assert False, f'Unknown signal type: {type(signal)}'