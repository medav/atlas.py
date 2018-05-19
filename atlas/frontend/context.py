from .. import model

circuit = None
context = []

def CreateCircuit(name):
    return model.Circuit(name)

def SetDefaultCircuit(_circuit):
    global circuit
    global context

    circuit = _circuit
    context = [circuit]

def CreateDefaultCircuit(name):
    SetDefaultCircuit(CreateCircuit(name))

class Module(model.Module):
    def __init__(self, _name):
        model.Module.__init__(self, _name)

    def PreElaborate(self):
        self.io.parent = self

    def Assign(self, signal, child):
        print('{} <= {}'.format(child, signal))

    def Elaborate():
        raise NotImplementedError()

class Condition():
    def __init__(self, _node):
        self.node = _node

    def __enter__(self):
        global context
        cond = model.Condition(self.node)
        context[-1].AddExpr(cond)
        context.append(cond)

    def __exit__(self, *args):
        global context
        context.pop()