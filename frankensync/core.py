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


_mutate_tree_to_coro = compose(
    transformers.StripToCoro().visit,
    transformers.MarkTree().visit,
)


_mutate_tree_to_function = compose(
    transformers.StripToFn().visit,
    transformers.MarkTree().visit,
)


@lru_cache
def frankensync(fn=None, *, namespace=None):
    # when run without params fill in namespace
    if fn is None:
        return partial(frankensync, namespace=namespace)

    if isinstance(namespace, list):
        raise ValueError("namespace must a a tuple not a list")
    elif isinstance(namespace, tuple):
        _namespace = {i.__name__: i for i in namespace}
    # None or None-like should get normalized to empty dict
    elif namespace is None:
        _namespace = {}
    else:
        _namespace = namespace

    _namespace =  merge(_namespace, FRANKENSYNC_BUILTIN_NAMESPACE)

    def build_functions():

        src = inspect.getsource(fn)


        # Im pretty sure the trees get mutated and that variable reassignements
        # are just references to the original ast objects.
        to_sync_tree = ast.parse(src)
        to_async_tree = copy.deepcopy(to_sync_tree)

        transformed_sync_tree = ast.fix_missing_locations(
            _mutate_tree_to_function(to_sync_tree)
        )

        transformed_async_tree = ast.fix_missing_locations(
            _mutate_tree_to_coro(to_async_tree)
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
