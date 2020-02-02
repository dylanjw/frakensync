import ast
import astor
import asyncio
import inspect
import time


import pytest
from pacro import utils

"""
TODO work out "macro templates" for async/sync functions
    TODO How? Using dumb classes? Type annotation? Functions? Special syntax?

    e.g.:

        @bisync
        def fn():
            await_maybe(asyncio.sleep(), sleep())

    or

        @bisync
        def fn():
            with pacro.block(condition):
                '''execute code if condition is met'''

            # builds await syntax if necessary
            pacro.assignment(symbol, val or expression)

            # builds await syntax if necessary
            pacro.statement(val or expression)


    or an entirely new syntax

        @bisync
        def fn():
            pacro = '''

        ***special syntax for creating macros

            '''

    or write code with await keyword that can be converted to native sync code!
        from pacro import (bisync, BisyncOption)
        @bisync
        async def fn():
            await BisyncOption(
                awaitable = asyncio.sleep(5),
                sync_fallback = sleep(5)
            )



TODO parse "macro templates" into coroutines or regular functions by rewriting ast.

"""


class BisyncOption:
    __slots__ = ['awaitable', 'sync_fallback']

    def __init__(self, awaitable, sync_fallback):
        self.awaitable = awaitable
        self.sync_fallback = sync_fallback

def function():
    time.sleep(5)

def bisync(fn):
    src = inspect.getsource(fn)
    target_src = inspect.getsource(function)
    print(src)
    _tree = ast.parse(src)
    _target_tree = ast.parse(target_src)
    print("\n\nBEFORE PROCESSING: \n" + astor.dump_tree(_tree))
    print("\n\nTARGET: \n" + astor.dump_tree(_target_tree))
    tree = ast.fix_missing_locations(
        CoroToFn().visit(_tree)
    )
    print("\n\nAFTER PROCESSING: \n" + astor.dump_tree(tree))
    code = compile(
        tree,
        filename="<bisync generated>",
        mode="exec")
    module = inspect.getmodule(fn)  # TODO Oh No Module Imports!!!
    exec(code, dir(module))
    return (namespace[fn.__name__])

    #if utils.is_async_caller():
    #    tree = ast.copy_location(CoroToCoro().visit(_tree))
    #else:
    #    tree = CoroToFn().visit(_tree)
    #compile(
    #    ast.fix_missing_locations(tree),
    #    filename="<ast>",
    #    mode="exec"
    #)


class CoroToFn(ast.NodeTransformer):
    def visit_AsyncFunctionDef(self, node):
        node = self.generic_visit(node)
        return ast.FunctionDef(
            name = node.name,
            args = node.args,
            body = node.body,
            decorator_list=[],  # TODO
            returns = None,  # TODO
            type_comment=None,  # TODO
            )

    def visit_Await(self, node):
        node = self.generic_visit(node)
        return node.value

    def visit_Call(self, node):
        expression = [
            keyword.value for keyword in node.keywords
            if keyword.arg == 'sync_fallback'].pop()
        if expression:
            node = expression
        return node


class CoroToCoro(ast.NodeTransformer):
    def visit_Await(self, node):
        assert isinstance(compile(node.value, 'ast', mode="single"), BisyncOption)
        awaitable = node.value.awaitable
        return ast.copy_location(
            ast.Await(awaitable),
            node
        )


def is_sync_caller():
    if utils.is_async_caller():
        return False
    return True


async def is_async_caller_coro():
    if utils.is_async_caller():
        await asyncio.sleep(0)
        return True
    return False


@pytest.mark.asyncio
async def test_dual_sleep_coro():
    assert(await is_async_caller_coro())


def test_dual_sleep_not_coro():
    assert(is_sync_caller())


@bisync
async def bisleep():
    await BisyncOption(
        awaitable = asyncio.sleep(5),
        sync_fallback = time.sleep(5),
    )


def test_bisleep_sync():
    bisleep()


#async def test_bisleep_async():
#    await bisleep()
