from firrtl import *


# circuit = Circuit("test")
# topmod = Module("top")
# circuit.AddModule(topmod)
# topmod.AddReg(Reg('foo', Type('UInt<8>')))


pt = ParseFirrtl(open('RefreshController.fir', 'r'))

print([mod.name for mod in pt.modules])