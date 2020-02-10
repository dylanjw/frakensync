import ast
import inspect
import os
from functools import partial, wraps

from toolz import complement

from .utils import hasattr_recursive

DEBUG = os.getenv("PACRO_DEBUG")

if DEBUG:
    import astor


class BisyncOption:
    __slots__ = ['awaitable', 'sync_fallback']

    def __init__(self, awaitable, sync_fallback):
        self.awaitable = awaitable
        self.sync_fallback = sync_fallback


def _bisync(fn=None, *, namespace=None):
    # when run without params fill in namespace
    if fn is None:
        return partial(_bisync, namespace=namespace)

    if isinstance(namespace, list):
        _namespace = {i.__name__: i for i in namespace}
    # None or None-like should get normalized to empty dict
    elif namespace is None:
        _namespace = {}
    else:
        _namespace = namespace

    @wraps(fn)
    def build_fn():
        src = inspect.getsource(fn)
        tree = ast.parse(src)
        if DEBUG:
            print(
                "BEFORE: \n\n%s" %
                astor.dump_tree(tree))

        transformed_tree = ast.fix_missing_locations(
            _parse_tree(tree)
        )

        if DEBUG:
            print(
                "AFTER: \n\n%s" %
                astor.dump_tree(transformed_tree))

        code = compile(
            transformed_tree,
            filename="<bisync generated>",
            mode="exec")
        exec(code, _namespace)
        return (_namespace[fn.__name__])

    return build_fn()


def _parse_tree(tree):
    MarkTree().visit(tree)
    CoroToFn().visit(tree)
    return tree

class BisyncFunctionDef(ast.AsyncFunctionDef):
    pass

class BisyncAwait(ast.Await):
    pass

class BisyncWith(ast.AsyncWith):
    pass

class BisyncFor(ast.AsyncFor):
    pass

def is_bisync_ast(ast_obj):
    if (hasattr_recursive(ast_obj, 'func', 'id') and
            ast_obj.func.id == 'bisync'):
        return True
    return False


not_bisync_ast = complement(is_bisync_ast)


class MarkTree(ast.NodeTransformer):
    def visit_AsyncFunctionDef(self, node):
        node = self.generic_visit(node)
        if any(map(is_bisync_ast, node.decorator_list)):
            node.decorator_list = list(filter(
                not_bisync_ast, node.decorator_list))
            node.__class__ = BisyncFunctionDef
        return node


class CoroToFn(ast.NodeTransformer):
    def visit_BisyncFunctionDef(self, node):
        node = self.generic_visit(node)
        return ast.FunctionDef(
            name=node.name,
            args=node.args,
            body=node.body,
            decorator_list=[],  # TODO
            returns=None,  # TODO
            type_comment=None,  # TODO
            )

    def visit_Await(self, node):
        return node
        #node = self.generic_visit(node)
        #return node.value

    def visit_Call(self, node):
        return node
        # TODO: Not every call will be *our* call. Parse our special "markers".
        #expression = [
        #    keyword.value for keyword in node.keywords
        #    if keyword.arg == 'sync_fallback'].pop()
        #if expression:
        #    node = expression
        #return node


class CoroToCoro(ast.NodeTransformer):
    def visit_Await(self, node):
        assert isinstance(
                compile(
                    node.value,
                    'ast',
                    mode="single"),
                BisyncOption)
        awaitable = node.value.awaitable
        return ast.copy_location(
            ast.Await(awaitable),
            node
        )

bisync = _bisync
