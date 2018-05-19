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