from .model import *
from .typespec import *

dirstr_map = {
    SignalTypes.INPUT: 'input',
    SignalTypes.OUTPUT: 'output',
    SignalTypes.INOUT: 'inout',
}

typestr_map = {
    SignalTypes.BITS: 'bits',
    SignalTypes.LIST: 'list',
    SignalTypes.BUNDLE: 'bundle'
}

def ForEachBits(signal):
    if signal.sigtype == SignalTypes.BITS:
        yield signal

    elif signal.sigtype == SignalTypes.LIST:
        for subsig in signal.fields:
            for bits in ForEachBits(subsig):
                yield bits

    elif signal.sigtype == SignalTypes.BUNDLE:
        for subsig in signal.fields:
            for bits in ForEachBits(signal.fields[subsig]):
                yield bits

    else:
        assert False

def ForEachIoBits(io_dict):
    for key in io_dict:
        signal = io_dict[key][1]
        parent_dir = signal.sigdir
        for bits in ForEachBits(signal):
            sigdir = signal.sigdir

            if signal.flipped:
                sigdir = flip_map[sigdir]

            yield bits, sigdir

def BuildConnectionTree(connections):
    """Build a binary tree of connections based off a connection AST.

    connections -- list of connections to convert
    """
    if len(connections) == 0:
        return None

    #
    # If the last assignment was un-predicated, all preceding assignments are
    # ignored by order of precedence, so just return it by itself.
    #

    if type(connections[-1]) is not ConnectionBlock:
        return connections[-1]

    #
    # If the last assignment is predicated with both paths containing non-zero
    # number of assignments, it's possible that one of the nodes deeper in the
    # tree hasn't fully filled out it's true / false paths. In order to ensure
    # correct behavior, the preceding connections in the current context are
    # promoted one level deeper (connections[:-1] + <true/false>_block).
    #

    if (len(connections[-1].true_block) > 0) and (len(connections[-1].false_block) > 0):
        return ConnectionTree(
            predicate=connections[-1].predicate,
            true_path=BuildConnectionTree(connections[:-1] + connections[-1].true_block),
            false_path=BuildConnectionTree(connections[:-1] + connections[-1].false_block))

    #
    # If the last assignment was predicated but one of the two paths has no
    # assignments, then defer to previous connections in this block.
    #

    assert not ((len(connections[-1].true_block) == 0) and (len(connections[-1].false_block) == 0))

    sub_ctree = BuildConnectionTree(connections[:-1])

    if len(connections[-1].true_block) > 0:
        return ConnectionTree(
            predicate=connections[-1].predicate,
            true_path=BuildConnectionTree(connections[:-1] + connections[-1].true_block),
            false_path=sub_ctree)

    if len(connections[-1].false_block) > 0:
        return ConnectionTree(
            predicate=connections[-1].predicate,
            true_path=sub_ctree,
            false_path=BuildConnectionTree(connections[:-1] + connections[-1].false_block))

def PrintCTree(ctree, indent=0):
    def WriteLine(line):
        print(' |  ' * indent + line)

    if ctree is None:
        WriteLine('None')
    elif type(ctree) is not ConnectionTree:
        WriteLine(str(ctree))
    else:
        WriteLine(f'Predicate: {ctree.predicate.name}')
        WriteLine('True path:')
        PrintCTree(ctree.true_path, indent + 1)
        WriteLine('False path:')
        PrintCTree(ctree.false_path, indent + 1)