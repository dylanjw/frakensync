import ast
import inspect

import pytest

from frankensync import frankensync, utils


def test_is_sync_caller_false():
    assert not utils.is_async_caller()


@pytest.mark.asyncio
async def test_is_async_caller_true():
    assert utils.is_async_caller()


@pytest.mark.asyncio
async def test_is_async_caller_true_with_stack_depth():
    def one():
        return utils.is_async_caller(stack_depth=1)
    def two():
        def inner():
            return utils.is_async_caller(stack_depth=2)
        return inner()

    assert one()
    assert two()


@pytest.mark.asyncio
async def test_is_async_caller_false_with_missing_stack_depth():
    def one():
        return utils.is_async_caller(stack_depth=0)
    def two():
        def inner():
            return utils.is_async_caller(stack_depth=0)
        return inner()

    assert not one()
    assert not two()


def test_repeatedly():
    assert utils.repeatedly(lambda x: x+1, 0, 5) == 5


class CountAccessesDescriptor:
    def __get__(self, obj, cls):
        obj.count += 1
        return obj

class A:
    attr = CountAccessesDescriptor()
    count = 0

def test_repeatedly_getattr():
    a = A()
    utils.repeatedly_getattr(a, 'attr', repeat=15)
    assert a.count == 15

def test_hasattr_recursive():
    class Bushel:
        amount = None

    class Apples:
        unit = Bushel

    class Cargo:
        fruit = Apples

    assert utils.hasattr_recursive(Cargo(), 'fruit', 'unit', 'amount')
    assert not utils.hasattr_recursive(Cargo(), 'unit', 'amount')


def test_unwrap_name_fn():
    fn = utils.unwrap_name_fn('count')
    assert fn(A()) == 0


decorated_with_parens_src = """
@decorator
@another_decorator
@frankensync()
async def dumb_coro():
    return True
"""

decorated_without_parens_src = """
@decorator
@another_decorator
@frankensync
async def dumb_coro():
    return True
"""

undecorated_src = """
@decorator
@another_decorator
async def dumb_coro():
    return True
"""


def test_not_frankensync_decorator_ast():
    _ast = ast.parse(undecorated_src)
    assert all(
        [
            utils.not_frankensync_ast_decorator(item) for item in
            _ast.body[0].decorator_list
        ]
    )


def test_not_frankensync_decorator_ast_false_without_parens():
    _ast = ast.parse(decorated_without_parens_src)
    assert not all(
        [
            utils.not_frankensync_ast_decorator(item) for item in
            _ast.body[0].decorator_list
        ]
    )


def test_is_frankensync_decorator_ast_with_parens():
    _ast = ast.parse(decorated_with_parens_src)
    assert any(
        map(
            utils.is_frankensync_ast_decorator,
            _ast.body[0].decorator_list
        )
    )


def test_is_frankensync_decorator_ast_without_parens():
    _ast = ast.parse(decorated_without_parens_src)
    assert any(
        map(
            utils.is_frankensync_ast_decorator,
            _ast.body[0].decorator_list
        )
    )
