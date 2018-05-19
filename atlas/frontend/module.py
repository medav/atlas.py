from .. import model

class Module(model.Module):
    def __init__(self, _name):
        model.Module.__init__(self, _name)

    def PreElaborate(self):
        self.io.parent = self
        self.context = [self]

    def ContainsSignal(self, signal):
        while signal.parent is not None and not issubclass(type(signal.parent), Module):
            signal = signal.parent

        return signal.parent == self

    def StartCondition(self, signal):
        assert self.ContainsSignal(signal)
        condition = model.Condition(signal)
        self.context[-1].AddStmt(condition)
        self.context.append(condition)

    def EndCondition(self):
        assert type(self.context[-1]) == model.Condition
        self.context.pop()

    def Wire(self, signal):
        signal.sigtype = model.Signal.WIRE
        self.context[-1].AddSignal(signal)

    def Reg(self, signal):
        signal.sigtype = model.Signal.REG
        self.context[-1].AddSignal(signal)

    def Assign(self, signal, child):
        self.context[-1].AddStmt(model.Assignment(child, signal))

    def Elaborate():
        raise NotImplementedError()