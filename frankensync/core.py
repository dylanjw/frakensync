import ast
import copy
import inspect
import os
from functools import lru_cache, partial

from toolz import compose, merge

import frankensync.transformers as transformers

from .utils import is_async_caller


class AwaitOrNot:
    __slots__ = ['awaitable', 'sync_fallback']

    def __init__(self, awaitable, sync_fallback):
        self.awaitable = awaitable
        self.sync_fallback = sync_fallback


FRANKENSYNC_BUILTIN_NAMESPACE = {'AwaitOrNot': AwaitOrNot}


@lru_cache(maxsize=100)
def frankensync(fn):

    _namespace =  fn.__globals__

    def build_functions():

        src = inspect.getsource(fn)


        # Im pretty sure the trees get mutated and that variable reassignements
        # are just references to the original ast objects.

        marked_tree = transformers.MarkTree().visit(ast.parse(src))

        to_sync_tree = copy.deepcopy(marked_tree)
        to_async_tree = copy.deepcopy(marked_tree)

        transformed_sync_tree = ast.fix_missing_locations(
            transformers.StripToFn().visit(to_sync_tree)
        )

        transformed_async_tree = ast.fix_missing_locations(
            transformers.StripToCoro().visit(to_async_tree)
        )

        async_code = compile(
            transformed_async_tree,
            filename="<frankensync generated>",
            mode="exec")
        exec(async_code, _namespace)

        sync_code = compile(
            transformed_sync_tree,
            filename="<frankensync generated>",
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
