import sys
sys.path.append('.')

import atlas.firrtl.emitter as emitter
from atlas.frontend import *

@Module
def FiniteStateMachine():
    io = Io({
        'a': Input(Bits(1)),
        'b': Input(Bits(1)),
        'cout': Output(Bits(2))
    })

    states = Enum(['init', 'a', 'b'])
    state = Reg(Bits(states.bitwidth))

    state.reset = states.init

    with io.a:
        state <<= states.a

    with io.b:
        state <<= states.b

    io.cout <<= state

    NameSignals(locals())

circuit = Circuit()
with circuit:
    top = FiniteStateMachine()

circuit.SetTop(top)
emitter.EmitFirrtl('fsm.fir', circuit)