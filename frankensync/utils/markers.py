import ast


class FrankensyncFunctionDef(ast.AsyncFunctionDef):
    pass

class FrankensyncAwait(ast.Await):
    async_value = None
    sync_value = None

class FrankensyncWith(ast.AsyncWith):
    pass

class FrankensyncFor(ast.AsyncFor):
    pass
