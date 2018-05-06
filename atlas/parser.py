from .backend import *

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

def ParseSignalType(type_str):
    return {
        'wire': Signal.WIRE,
        'reg': Signal.REG,
        'node': Signal.NODE,
        'input': Signal.INPUT,
        'output': Signal.OUTPUT,
    }[type_str]

def ParseSignal(context, line):
    regex = re.compile('(wire|reg|input|output) ([a-zA-Z_0-9]+)\\W*:\\W*(.*)(@\\[.*\\])?')
    m = regex.match(line.strip())

    signal = Signal(m.groups('')[1].strip())
    signal.sigtype = ParseSignalType(m.groups('')[0].strip())

    dtype = Signal.ParseDtype(m.groups('')[2].strip())
    # info = m.groups('')[3].strip()

    return Signal(sigtype, name, dtype, info)

    context[-1].AddSignal(Signal.FromString(line))
    pass

def ParseNode(context, line):
    context[-1].AddNode(Node.FromString(line))
    pass

def ParseSkip(context, line):
    pass

def ParseWhen(context, line):
    condition_str = line.strip().replace(':', ' ').split(' ')[1]
    cond = Condition(condition_str)
    context[-1].AddExpr(cond)
    context.append(cond)

def ParseElse(context, line):
    condition_str = 'else'
    assert type(context[-1].exprs[-1]) is Condition
    cond_else = Condition('else')
    context[-1].exprs[-1].cond_else = cond_else
    context.append(cond_else)

parse_vector = {
    'input': ParseSignal,
    'output': ParseSignal,
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