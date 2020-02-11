import ast

from toolz import compose

from .utils import (
    hasattr_recursive,
    is_frankensync_ast,
    not_frankensync_ast,
    unwrap_name_fn
)
from .utils.markers import (
    FrankensyncAwait,
    FrankensyncFor,
    FrankensyncFunctionDef,
    FrankensyncWith
)


def is_AwaitOrNot(ast_obj):
    if (hasattr_recursive(ast_obj, 'func', 'id') and
            ast_obj.func.id == 'AwaitOrNot'):
        return True
    return False


def filter_AwaitOrNot_by_keyword(keyword):
    if keyword not in ['awaitable', 'sync_fallback']:
        raise ValueError("keyword must be one of: 'awaitable' or 'sync_fallback'")
    def inner(iterable):
        for val in iterable:
            if val.arg == keyword:
                return val
    return inner


get_awaitable_value = compose(
    unwrap_name_fn('value'),
    filter_AwaitOrNot_by_keyword('awaitable'),
)


get_sync_fallback_value = compose(
    unwrap_name_fn('value'),
    filter_AwaitOrNot_by_keyword('sync_fallback'),
)


class MarkTree(ast.NodeTransformer):
    """Update Tree with Custom AST types

    Frankensync's modifies the AST in two passes.
    MarkTree makes the first pass. It is concerned identification of frankensync
    AST targets and syntax validation. Targets are "marked" with custom ast
    objects so later passes can visit those objects.

    1. Convert frankensync wrapped AsyncFunctionDef type to FrankensyncFunctionDef
    2. Convert Await type to Biwait type.
    3. Convert AsyncWith ...
    3. Convert AsyncFor ...
    """
    def visit_AsyncFunctionDef(self, node):
        node = self.generic_visit(node)
        if any(map(is_frankensync_ast, node.decorator_list)):
            # Remove `frankensync` from decorator list
            node.decorator_list = list(filter(
                not_frankensync_ast, node.decorator_list))
            node.__class__ = FrankensyncFunctionDef
        return node

    def visit_Await(self, node):
        # TODO: Support defining an async def inside of a frankensync decorated async def.
        # Right now, all `await` keywords must be paired with a AwaitOrNot, but
        # this breaks the ability to have nested async function definitions.
        if is_AwaitOrNot(node.value):
            node.__class__ = FrankensyncAwait
            # TODO Something is screwy here. The purpose is to move the ast values for
            # sync/async variants into custom fields in the FrankensyncAwait ast node type.
            node.async_value = get_awaitable_value(node.value.keywords)
            node.sync_value = get_sync_fallback_value(node.value.keywords)
            node.value = None
        return node

    def visit_AsyncFor(self, node):
        return node

    def visit_AsyncWith(self, node):
        return node


class StripToFn(ast.NodeTransformer):
    def visit_FrankensyncFunctionDef(self, node):
        node = self.generic_visit(node)

        # Do I really want to do it this way?
        # or should I compile the functions in
        # their own namespaces?
        node.name = node.name + "_SYNC"
        return ast.FunctionDef(
            name=node.name,
            args=node.args,
            body=node.body,
            decorator_list=[],  # TODO
            returns=None,  # TODO
            type_comment=None,  # TODO
            )

    def visit_FrankensyncAwait(self, node):
        node = node.sync_value
        return node


class StripToCoro(ast.NodeTransformer):
    def visit_FrankensyncFunctionDef(self, node):
        node = self.generic_visit(node)
        node.name = node.name + "_ASYNC"
        node.__class__ = ast.AsyncFunctionDef
        return node

    def visit_FrankensyncAwait(self, node):
        node.value = node.async_value
        return node
