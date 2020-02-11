import ast
import copy
import inspect
import os
from functools import partial, wraps

from toolz import complement, compose, merge

from .utils import hasattr_recursive, is_async_caller

DEBUG = os.getenv("PACRO_DEBUG")

if DEBUG:
    import astor



class BisyncOption:
    __slots__ = ['awaitable', 'sync_fallback']

    def __init__(self, awaitable, sync_fallback):
        self.awaitable = awaitable
        self.sync_fallback = sync_fallback


PACRO_BUILTIN_NAMESPACE = {'BisyncOption': BisyncOption}


async def async_target():
    await asyncio.sleep(0)
    return "success"


def sync_target():
    time.sleep(0)
    return "success"


def print_target_function(fn):
    tree_str = compose(
        astor.dump_tree,
        ast.parse,
        inspect.getsource,
    )(fn)
    print("!!!!!!TARGET!!!!!!: " + tree_str)


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

    _namespace =  merge(_namespace, PACRO_BUILTIN_NAMESPACE)

    def build_functions():

        src = inspect.getsource(fn)


        # Im pretty sure the trees get mutated and that variable reassignements
        # are just references to the original ast objects.
        to_sync_tree = ast.parse(src)
        to_async_tree = copy.deepcopy(to_sync_tree)

        if DEBUG:
            print(
                "BEFORE: \n\n%s" %
                astor.dump_tree(to_async_tree))

        transformed_sync_tree = ast.fix_missing_locations(
            _mutate_tree_to_function(to_sync_tree)
        )

        transformed_async_tree = ast.fix_missing_locations(
            _mutate_tree_to_coro(to_async_tree)
        )

        if DEBUG:
            print(
                "AFTER: \n\n%s" %
                astor.dump_tree(transformed_async_tree))

        #print_target_function(async_target)

        async_code = compile(
            transformed_async_tree,
            filename="<bisync generated>",
            mode="exec")
        exec(async_code, _namespace)

        sync_code = compile(
            transformed_sync_tree,
            filename="<bisync generated>",
            mode="exec")
        exec(sync_code, _namespace)

        new_fn = _namespace[fn.__name__ + "_SYNC"]
        new_coro = _namespace[fn.__name__ + "_ASYNC"]

        return new_fn, new_coro


    new_fn, new_coro = build_functions()

    def inner(*args, **kwargs):
        if is_async_caller(stack_depth=1):
            return new_coro(*args, **kwargs)
        else:
            return new_fn(*args, **kwargs)

    return inner



class BisyncFunctionDef(ast.AsyncFunctionDef):
    pass

class BisyncAwait(ast.Await):
    async_value = None
    sync_value = None

class BisyncWith(ast.AsyncWith):
    pass

class BisyncFor(ast.AsyncFor):
    pass

def is_bisync_ast(ast_obj):
    if (hasattr_recursive(ast_obj, 'func', 'id') and
            ast_obj.func.id == 'bisync'):
        return True
    return False

def is_BisyncOption(ast_obj):
    if (hasattr_recursive(ast_obj, 'func', 'id') and
            ast_obj.func.id == 'BisyncOption'):
        return True
    return False

def filter_BisyncOption_by_keyword(keyword):
    if keyword not in ['awaitable', 'sync_fallback']:
        raise ValueError("keyword must be one of: 'awaitable' or 'sync_fallback'")
    def inner(iterable):
        for val in iterable:
            if val.arg == keyword:
                return val
    return inner


def unwrap_name_fn(name):
    def inner(object):
        return getattr(object, name)

    return inner


get_awaitable_value = compose(
    unwrap_name_fn('value'),
    filter_BisyncOption_by_keyword('awaitable'),
)


get_sync_fallback_value = compose(
    unwrap_name_fn('value'),
    filter_BisyncOption_by_keyword('sync_fallback'),
)


not_bisync_ast = complement(is_bisync_ast)


class MarkTree(ast.NodeTransformer):
    """Update Tree with Custom AST types

    Bisync's modifies the AST in two passes.
    MarkTree makes the first pass. It is concerned identification of bisync
    AST targets and syntax validation. Targets are "marked" with custom ast
    objects so later passes can visit those objects.

    1. Convert bisync wrapped AsyncFunctionDef type to BisyncFunctionDef
    2. Convert Await type to Biwait type.
    3. Convert AsyncWith ...
    3. Convert AsyncFor ...
    """
    def visit_AsyncFunctionDef(self, node):
        node = self.generic_visit(node)
        if any(map(is_bisync_ast, node.decorator_list)):
            # Remove `bisync` from decorator list
            node.decorator_list = list(filter(
                not_bisync_ast, node.decorator_list))
            node.__class__ = BisyncFunctionDef
        return node

    def visit_Await(self, node):
        # TODO: Support defining an async def inside of a bisync decorated async def.
        # Right now, all `await` keywords must be paired with a BisyncOption, but
        # this breaks the ability to have nested async function definitions.
        if is_BisyncOption(node.value):
            node.__class__ = BisyncAwait
            # TODO Something is screwy here. The purpose is to move the ast values for
            # sync/async variants into custom fields in the BisyncAwait ast node type.
            node.async_value = get_awaitable_value(node.value.keywords)
            node.sync_value = get_sync_fallback_value(node.value.keywords)
            node.value = None
        return node

    def visit_AsyncFor(self, node):
        return node

    def visit_AsyncWith(self, node):
        return node


class StripToFn(ast.NodeTransformer):
    def visit_BisyncFunctionDef(self, node):
        node = self.generic_visit(node)

        # Do I really want to do it this way?
        # or should I have 2 separate namespaces?
        node.name = node.name + "_SYNC"
        return ast.FunctionDef(
            name=node.name,
            args=node.args,
            body=node.body,
            decorator_list=[],  # TODO
            returns=None,  # TODO
            type_comment=None,  # TODO
            )

    def visit_BisyncAwait(self, node):
        node = node.sync_value
        return node


class StripToCoro(ast.NodeTransformer):
    def visit_BisyncFunctionDef(self, node):
        node = self.generic_visit(node)
        node.name = node.name + "_ASYNC"
        node.__class__ = ast.AsyncFunctionDef
        return node

    def visit_BisyncAwait(self, node):
        node.value = node.async_value
        return node


_mutate_tree_to_coro = compose(
    StripToCoro().visit,
    MarkTree().visit,
)


_mutate_tree_to_function = compose(
    StripToFn().visit,
    MarkTree().visit,
)

bisync = _bisync
