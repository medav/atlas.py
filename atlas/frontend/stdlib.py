from .. import model
from .base import *
from .signal import *

__all__ = [
    'Cat'
]

def Cat(signals):
    if len(signals) == 1:
        return signals[0]

    elif len(signals) == 2:
        n = Node('cat', signals)
        CurrentContext().AddNode(n)
        return n

    else:
        half = int(len(signals) / 2)
        n1 = Cat(signals[:half])
        n2 = Cat(signals[half:])
        return Cat([n1, n2])