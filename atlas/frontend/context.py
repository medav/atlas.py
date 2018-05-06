import ..backend as backend

circuit = None
context = []

def CreateCircuit(name):
    return backend.Circuit(name)

def SetDefaultCircuit(_circuit):
    circuit = _circuit
    context = [circuit]

def CreateDefaultCircuit(name):
    SetDefaultCircuit(CreateCircuit(name))

class Module():
    def __init__(self, _name):
        self.name = _name

    def Io(self):
        raise NotImplementedError()

    def Elaborate():
        raise NotImplementedError()

class Condition():
    def __init__(self, _node):
        self.node = _node

    def __enter__(self):
        cond = backend.Condition(self.node)
        context[-1].AddExpr(cond)
        context.append(cond)

    def __exit__(self, *args):
        context.pop()

