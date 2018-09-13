from . import model as M
from .typespec import *

dirstr_map = {
    M.SignalDir.INPUT: 'input',
    M.SignalDir.OUTPUT: 'output',
    M.SignalDir.INOUT: 'inout',
}

valid_rhs_types = {int, bool}

def ForEachBits(signal):
    if type(signal) is M.BitsSignal:
        yield signal

    elif type(signal) is M.ListSignal:
        for subsig in signal.fields:
            for bits in ForEachBits(subsig):
                yield bits

    elif type(signal) is M.BundleSignal:
        for subsig in signal.fields:
            for bits in ForEachBits(signal.fields[subsig]):
                yield bits

    else:
        assert False, f'Unknown signal type: {type(signal)}'

def ZipBits(sig_a, sig_b):
    if type(sig_a) is M.BitsSignal:
        assert type(sig_b) is M.BitsSignal
        assert sig_a.width == sig_b.width

        yield (sig_a, sig_b)

    elif type(sig_a) is M.ListSignal:
        assert type(sig_b) is M.ListSignal
        assert len(sig_a.fields) == len(sig_b.fields)

        for i in range(len(sig_a.fields)):
            for pair in ZipBits(sig_a.fields[i], sig_b.fields[i]):
                yield pair

    elif type(sig_a) is M.BundleSignal:
        assert type(sig_b) is M.BundleSignal
        assert sig_a.fields.keys() == sig_b.fields.keys()

        for key in sig_a.fields:
            for pair in ZipBits(sig_a.fields[key], sig_b.fields[key]):
                yield pair

    else:
        assert False, f'Unknown signal type: {type(signal)}'

def ForBitsInModule(module):
    for signal in module.signals:
        for bits in ForEachBits(signal):
            yield bits

def ForEachIoBits(io_dict : dict):
    for key in io_dict:
        for bits in ForEachBits(io_dict[key]):
            yield bits

def GetDirection(signal):
    absolute_dirs = {M.SignalDir.INPUT, M.SignalDir.OUTPUT, M.SignalDir.INOUT}

    if signal.meta.sigdir in absolute_dirs:
        return signal.meta.sigdir
    else:
        if signal.meta.parent is None:
            assert signal.meta.sigdir == M.SignalDir.INHERIT
            return M.SignalDir.INHERIT

        parent_dir = GetDirection(signal.meta.parent)

        if signal.meta.sigdir == M.SignalDir.INHERIT:
            return parent_dir
        else:
            assert signal.meta.sigdir == M.SignalDir.FLIPPED
            return M.flip_map[parent_dir]


def InsertConnection(lhs, predicate, rhs):
    """Insert a predicated connection into a signal's connection list

    This is done by walking through the current predicate and producing
    connection blocks in this signal's ast until a point is reached where this
    connection can be inserted.
    """

    assert type(lhs) is M.BitsSignal
    assert (type(rhs) is M.BitsSignal) or (type(rhs) in valid_rhs_types)

    block = lhs.connections

    for (signal, path) in predicate:
        if (len(block) > 0) and \
            (type(block[-1]) is M.ConnectionBlock) and \
            (block[-1].predicate is signal):

            block = block[-1].true_block if path else block[-1].false_block
        else:
            cb = M.ConnectionBlock(signal)
            block.append(cb)
            block = cb.true_block if path else cb.false_block

    block.append(rhs)

def BuildConnectionTree(connections, debug_name=None):
    """Build a binary tree of connections based off a connection AST.

    connections -- list of connections to convert
    """

    if len(connections) == 0:
        return None

    #
    # If the last assignment was un-predicated, all preceding assignments are
    # ignored by order of precedence, so just return it by itself.
    #

    if type(connections[-1]) is not M.ConnectionBlock:
        return connections[-1]

    #
    # If there is a single connection in the list and it _is_ a connection
    # block, then it should have connections in both true and false paths, or
    # the assignment tree is incomplete (which will result in compilable code).
    #

    if len(connections) == 1:
        assert (len(connections[-1].true_block) > 0) and \
            (len(connections[-1].false_block) > 0), \
            f'Signal {debug_name} has incomplete connection ast'

    #
    # If the last assignment is predicated with both paths containing non-zero
    # number of assignments, it's possible that one of the nodes deeper in the
    # tree hasn't fully filled out it's true / false paths. In order to ensure
    # correct behavior, the preceding connections in the current context are
    # promoted one level deeper (connections[:-1] + <true/false>_block).
    #

    if (len(connections[-1].true_block) > 0) and \
        (len(connections[-1].false_block) > 0):

        return M.ConnectionTree(
            predicate=connections[-1].predicate,
            true_path=BuildConnectionTree(
                connections[:-1] + connections[-1].true_block, debug_name),

            false_path=BuildConnectionTree(
                connections[:-1] + connections[-1].false_block, debug_name))

    #
    # If the last assignment was predicated but one of the two paths has no
    # assignments, then defer to previous connections in this block.
    #

    assert not ((len(connections[-1].true_block) == 0) and \
        (len(connections[-1].false_block) == 0))

    sub_ctree = BuildConnectionTree(connections[:-1], debug_name)

    if len(connections[-1].true_block) > 0:
        return M.ConnectionTree(
            predicate=connections[-1].predicate,
            true_path=BuildConnectionTree(
                connections[:-1] + connections[-1].true_block, debug_name),
            false_path=sub_ctree)

    if len(connections[-1].false_block) > 0:
        return M.ConnectionTree(
            predicate=connections[-1].predicate,
            true_path=sub_ctree,
            false_path=BuildConnectionTree(
                connections[:-1] + connections[-1].false_block, debug_name))

def PrintCTree(ctree, indent=0):
    def WriteLine(line):
        print(' |  ' * indent + line)

    if ctree is None:
        WriteLine('None')
    elif type(ctree) is not M.ConnectionTree:
        WriteLine(str(ctree))
    else:
        WriteLine(f'Predicate: {ctree.predicate.name}')
        WriteLine('True path:')
        PrintCTree(ctree.true_path, indent + 1)
        WriteLine('False path:')
        PrintCTree(ctree.false_path, indent + 1)