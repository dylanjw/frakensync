import ast


class FrankensyncFunctionDef(ast.AsyncFunctionDef):
    pass

class FrankensyncAwaitOrNot(ast.Await):
    async_value = None
    sync_value = None

class FrankensyncAwait(ast.Await):
    pass

class FrankensyncWith(ast.AsyncWith):
    pass

class FrankensyncFor(ast.AsyncFor):
    pass
