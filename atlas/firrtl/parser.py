from ..model import *
from .shared import *

def ParseCircuit(context, line):
    if not line.startswith('circuit'):
        raise RuntimeError('Expected keyword: circuit')

    name = line.replace(':', '').strip().split(' ')[1]
    circuit = Circuit(name)
    context.append(circuit)

def ParseModule(context, line):
    if not line.strip().startswith('module'):
        raise RuntimeError('Expected keyword: module')

    name = line.replace(':', ' ').strip().split(' ')[1]
    module = Module(name)
    context[-1].AddModule(module)
    context.append(module)

def ParseBitsType(type_string):
    m = bits_regex.match(type_string.strip())
    assert m is not None
    signed = True is m.groups('')[0] == 'S' else False
    bitwidth = int(m.groups('')[1])
    length = int(m.groups('1')[3])
    return Bits(bitwidth, _length=length, _signed=signed)

def SubSignals(type_string):
    name_start = 1
    name_end = 2
    end = False

    while not end:
        while type_string[name_end] != ':':
            name_end += 1
        
        name_part = type_string[name_start:name_end].strip().split(' ')
        assert len(name_part) == 1 or len(name_part) == 2

        flip = False
        if len(name_part) == 2:
            assert name_part[0] == 'flip'
            flip = True

            name = name_part[1]
        
        else:
            name = name_part[0]

        type_start = name_end + 1
        type_end = type_start

        sub_expr = 0

        while type_string[type_end] != ',' or sub_expr > 0:
            if type_string[type_end] == '{':
                sub_expr += 1

            if type_string[type_end] == '}':
                sub_expr -= 1
                if sub_expr == -1:
                    end = True
                    break

            type_end += 1

        subtype_string = type_string[type_start:type_end].strip()

        yield (flip, name, subtype_string)

        name_start = type_end + 1
        name_end = name_start + 1
        
def ParseBundleType(type_string):
    bundle_dict = {}
    for ss in SubSignals(type_string):
        signal = ParseSignalType(ss[2])
        signal.name = ss[1]
        if ss[0]:
            signal.sigdir = Signal.FLIP
        bundle_dict[signal.name] = signal.name

    return Bundle(bundle_dict)

def ParseSignalType(type_string):
    if type_string.startswith('{'):
        return ParseBundleType(type_string)
    else:
        return ParseBitsType(type_string)

def ParseIo(context, line):
    m = io_regex.match(line.strip())
    assert m is not None
    signal = ParseSignalType(m.groups('')[2].strip())
    signal.sigdir = signal_str_dir[m.groups('')[0].strip()]
    context[-1].AddSignal(signal)

def ParseSignal(context, line):
    m = signal_regex.match(line.strip())
    assert m is not None
    signal = Signal(m.groups('')[1].strip())
    signal.sigtype = signal_type_name_map[m.groups('')[0].strip()]
    dtype = ParseSignalType(m.groups('')[2].strip())
    context[-1].AddSignal(Signal.FromString(line))

def ParseNode(context, line):
    m = node_regex.match(line.strip())
    assert m is not None
    name = m.groups('')[0].strip()
    expr = m.groups('')[1].strip()
    info = m.groups('')[2].strip()
    node = Node(name, expr, info)
    context[-1].AddNode(node)

def ParseSkip(context, line):
    pass

def ParseWhen(context, line):
    condition_str = line.strip().replace(':', ' ').split(' ')[1]
    cond = Condition(condition_str)
    context[-1].AddStmt(cond)
    context.append(cond)

def ParseElse(context, line):
    condition_str = 'else'
    assert type(context[-1].exprs[-1]) is Condition
    cond_else = Condition('else')
    context[-1].exprs[-1].cond_else = cond_else
    context.append(cond_else)

parse_vector = {
    'input': ParseIo,
    'output': ParseIo,
    'reg': ParseSignal,
    'wire': ParseSignal,
    'node': ParseNode,
    'skip': ParseSkip,
    'when': ParseWhen,
    'else': ParseElse
}

def ParseStatement(context, line):
    line_stripped = line.strip()
    for key in parse_vector:
        if line_stripped.startswith(key):
            parse_vector[key](context, line)
            return
    
    context[-1].AddExpr(line.strip())

def ParseFirrtl(f):
    """Parse an opened firrtl into an Atlas model"""

    indent_level = 0
    prev_indent_level = 0
    indent_spaces = 0
    context = []
    line_num = 0

    try:
        for line in f:
            line_num += 1
            if len(line.strip()) == 0 or line.strip().startswith(';'):
                continue

            if line.startswith(' '):
                if indent_spaces == 0:
                    indent_spaces = len(line) - len(line.lstrip())

                indent_level = int((len(line) - len(line.lstrip())) / indent_spaces)
            else:
                indent_level = 0

            if indent_level < prev_indent_level:
                for i in range(prev_indent_level - indent_level):
                    context.pop()

            if indent_level == 0:
                ParseCircuit(context, line)
            elif indent_level == 1:
                ParseModule(context, line)
            else:
                ParseStatement(context, line)

            prev_indent_level = indent_level

    except Exception as e:
        print('Exception at line {}'.format(line_num))
        print('line = \"{}\"'.format(line.rstrip()))
        print('indent_level = {}'.format(indent_level))
        print('prev_indent_level = {}'.format(prev_indent_level))
        print([c.__str__() for c in context])
        raise

    return context[0]