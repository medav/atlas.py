from dataclasses import dataclass

from . import model as M

def Bits(width, signed=False, flipped=False):
    return {
        'width': width,
        'signed': signed,
        'flipped': flipped
    }

def IsBits(typespec):
    if type(typespec) is not dict:
        return False
    else:
        return \
            (set(typespec.keys()) == {'width', 'signed', 'flipped'}) and \
            (type(typespec['width']) is int)

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
        return Bits(signal.width, signal.signed, signal.flipped)

    elif type(signal) is M.ListSignal:
        return [
            TypespecOf(signal.fields[0]) for _ in range(len(signal.fields))
        ]

    elif type(signal) is M.BundleSignal:
        return { key: TypespecOf(signal.fields[key]) for key in signal.fields }

    else:
        assert False, f'Unknown signal type: {type(signal)}'