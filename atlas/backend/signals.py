
class Signal():
    OUTPUT = 0
    INPUT = 1
    WIRE = 2
    REG = 3
    NODE = 4

    def __init__(self, _name):
        self.sigtype = Signal.WIRE
        self.name = _name
        self.parent = None

    def SetParent(self, _parent):
        self.parent = _parent

    def ChildAssign(self, child, signal):
        assert self.parent is not None
        self.parent.ChildAssign(child, signal)

    def Assign(self, signal):
        assert self.parent is not None
        self.parent.ChildAssign(self, signal)

    def __str__(self):
        assert self.parent is not None
        
        return self.parent.__str__() + '.' + self.name

class Bits(Signal):
    def __init__(self, _width, _signed=False):
        Signal.__init__(self, 'bits')
        self.width = _width
        self.signed = _signed
        self.parent = None

class Bundle(Signal):
    def __init__(self, _name, _dict):
        Signal.__init__(self, _name)
        self.signal_names = []

        for name in _dict:
            self.signal_names.append(name)
            _dict[name].name = name
            _dict[name].SetParent(self)

        self.__dict__.update(_dict)

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index >= len(self.signal_names):
            raise StopIteration

        signal = self.__dict__[self.signal_names[self.index]]
        self.index += 1

        return signal

    def __getitem__(self, key):
        return self.__dict__[key]

def Signed(signal):
    signal.signed = True
    return

def Unsigned(signal):
    signal.signed = False
    return

def Flip(signal):
    if signal.sigtype == Signal.INPUT:
        signal.sigtype = Signal.OUTPUT
    else:
        signal.sigtype = Signal.INPUT

    return signal

def Input(signal):
    signal.sigtype = Signal.INPUT
    return signal

def Output(signal):
    signal.sigtype = Signal.OUTPUT
    return signal

def Io(_dict):
    return Bundle('io', _dict)
