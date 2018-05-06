from .. import backend

circuit = None
context = []

def CreateCircuit(name):
    return backend.Circuit(name)

def SetDefaultCircuit(_circuit):
    global circuit
    global context

    circuit = _circuit
    context = [circuit]

def CreateDefaultCircuit(name):
    SetDefaultCircuit(CreateCircuit(name))

class Module(backend.Module):
    def __init__(self, _name):
        backend.Module.__init__(self, _name)

    def PreElaborate(self):
        self.io.SetParent(self)

    def ChildAssign(self, child, signal):
        print('{} <= {}'.format(child, signal))

    def Elaborate():
        raise NotImplementedError()

class Condition():
    def __init__(self, _node):
        self.node = _node

    def __enter__(self):
        global context
        cond = backend.Condition(self.node)
        context[-1].AddExpr(cond)
        context.append(cond)

    def __exit__(self, *args):
        global context
        context.pop()

class Else():
    def __init__(self):
        pass

    def __enter__(self):
        global context
        cond = backend.Condition('else')
        context[-1].AddExpr(cond)
        context.append(cond)

    def __exit__(self, *args):
        global context
        context.pop()