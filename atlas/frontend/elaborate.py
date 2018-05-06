from . import context as ctx


def Elaborate(module):
    assert ctx.circuit is not None
    assert len(ctx.context) == 1

    ctx.context.append(module)
    ctx.circuit.AddModule(module)
    module.PreElaborate()
    module.Elaborate()
    ctx.context.pop()

    return ctx.circuit