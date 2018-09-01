# Atlas

A Python-based hardware generator framework targeting Verilog

# Installation
Requirements:
* [Python 3.7+](https://www.python.org/)
* pip

Atlas is not yet distributed on PyPI. For now, install by running:
```
$ pip install .
```

In the Atlas folder.

# Crash Course
Below is a full working example of a N-bit ripple-carry adder:

```python
from atlas import *

def FullAdder(cin, a, b):
    a_xor_b = a ^ b
    sum_out = a_xor_b ^ cin
    cout = (a & b) | (a_xor_b & cin)
    return sum_out, cout

@Module
def RippleAdder(n):
    io = Io({
        'a': Input(Bits(n)),
        'b': Input(Bits(n)),
        'cin': Input(Bits(1)),
        'sum_out': Output(Bits(n)),
        'cout': Output(Bits(1))
    })

    carry = io.cin
    out_arr = Wire([Bits(1) for i in range(n)])

    for i in range(n):
        sum_i, carry = FullAdder(carry, io.a(i, i), io.b(i, i))
        out_arr[i] <<= sum_i

    io.cout <<= carry
    io.sum_out <<= Cat([out_arr[n - i - 1] for i in range(n)])

    NameSignals(locals())

circuit = Circuit('adder')

with Context(circuit):
    top = RippleAdder(8)

circuit.top = top
EmitCircuit(circuit, 'adder.v')
```

Modules in Atlas are denoted by the `@Module` Python decorator. Module functions are callable like other functions to produce a module object that can be added to a circuit. Here a single module - a `RippleCarry` is created. The additional function `FullAdder` is not a module by itself but simply allows a repeated section of logic to be organized into its own section.

The `<<=` operator in Python is overloaded to be the universal connection operator. It is used to attach one signal to another.

Typical Python operators are hooked to enable intuitive description of logic operations (E.g. `&`, `|`, `+`, etc... for bitwise _and_, _or_, and _add_).

# FAQ
## Q. Is this Chisel?
A. Essentially yes, but in Python, and slightly different design choices. Also, all of the Atlas codebase it MIT licensed (I did not look at any of Chisel's source code while writing this).

## Q. Is this _not_ an embedded language / DSL?
A. The answer is: _kind of_. It's mostly just a matter of marketing: Chisel markets itself as a "scala-embedded-language" while Atlas is intended to be viewed as a "framework". It's the Python you know and love with library constructs to build up a model of a circuit then export it to Verilog. Like Chisel, though, Atlas provides some syntactic sugars to make hardware description a bit more DSL-esque.

## Q. Why not ________ HDL?
A. Most approaches have advantages and disadvantages. Use this if after trying it, you think the former outweighs the latter.
