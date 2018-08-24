# Atlas

A Python-based hardware generator framework targeting Verilog

# Installation
Requirements:
* [Python 3.7+](https://www.python.org/)

To install, just run:
```
$ python setup.py install
```

# FAQ
## Q. Is this Chisel?
A. Essentially yes, but in Python, and slightly different design choices. Also,
all of the Atlas codebase it MIT licensed (I did not look at any of Chisel's
source code while writing this).

## Q. Is this _not_ an embedded language / DSL?
A. The answer is: _kind of_. It's mostly just a matter of marketing: Chisel markets
itself as a "scala-embedded-language" while Atlas is intended to be viewed as a
"framework". It's the Python you know and love with library constructs to build
up a model of a circuit then export it to Verilog. Like Chisel, though, Atlas
provides some syntactic sugars to make hardware description a bit more DSL-esque.
