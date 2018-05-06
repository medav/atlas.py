import ..backend as backend

class Signal():
    def __init__(self, _name):
        self.dir_in = False
        self.name = _name
        self.parent = _parent

    def SetParent(self, _parent):
        self.parent = _parent

class Bits(Signal):
    def __init__(self, _name, _width, _signed=False):
        Signal.__init__(_name)
        self.width = _width
        self.signed = _signed
        self.parent = None

class Bundle(Signal):
    def __init__(self, _name, _dict):
        Signal.__init__(_name)
        self.signals = _dict

        for _, signal in self.signals:
            signal.SetParent(self)

    def __getitem__(key):
        return self.signals[key]

def Signed(signal):
    signal.signed = True
    return

def Unsigned(signal):
    signal.signed = False
    return

def Flip(signal):
    signal.dir_in = not signal.dir_in
    return signal

def Input(signal):
    signal.dir_in = True
    return signal

def Output(signal):
    signal.dir_in = False
    return signal

def Io(_dict):
    return Bundle('io', _dict)