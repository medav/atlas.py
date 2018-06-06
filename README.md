# Atlas

A Python-based hardware generator framework targeting firrtl

## FAQ
### Q. Is this Chisel?
A. Essentially yes, but in Python, and slightly different design choices. Also,
all of the Atlas codebase it MIT licensed (I did not look at any of Chisel's 
source code while writing this, only the firrtl spec).

### Q. Is this _not_ an embedded language / DSL?
A. The answer is _kind of_. It's mostly just a matter of marketing: Chisel markets 
itself as a "scala-embedded-language" while Atlas is intended to be viewed as a
"framework" or "library". It's the Python you know and love with library constructs
to build up a model of a circuit then export it to firrtl. Like Chisel, too, Atlas
provides some syntactic sugars to make hardware description a bit more intuitive.