from dataclasses import dataclass

__all__ = [
    'Bits',
    'IsBits',
    'CompareTypespec'
]

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
