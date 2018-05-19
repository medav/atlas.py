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