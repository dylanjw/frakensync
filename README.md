# pacro

Pythons `async` and `await` syntax makes writing and maintaining asynchronous code a dream.
Except when you are maintaining a library with both a synchronous and asynchronous API. In that
case, code reuse becomes a labyrinth of locked doors and `loop.run_until_complete`. This is 
because introducing coroutines requires that you await on coroutines that await on couroutines that awai[...].
Its turtles all the way down.

## Be kind to turtles.

Wouldn't it be cool if we could write some code that could be expanded into both native
synchronous and native asynchronous variants, without having to jam one type of turtle into the 
other?


``` python
from pacro.async import (
    bisync,
    await_assign,
    await_return,
)


@bisync
def update_conversion_rate_middleware(make_request):
    def middleware(method, params)
        rate = params.get('rate', False)
        if rate:
            rate = await_assign(
                coro = coro_pull_conversion_rate(price), 
                sync = sync_pull_conversion_rate(price),
            )
            params['rate'] = rate

        await_return(make_request(method, params))
```

## How the hell does this work?

The above `update_conversion_rate_middleware` function gets expanded by modifying the ast into
something equivalent to the following:

``` python
async update_conversion_rate_middleware_coro(make_request):
    def middleware(method, params)
        rate = params.get('rate', False)
        if rate:
            rate = await coro_pull_conversion_rate(price) 
            params['rate'] = rate

        return await make_request(method, params)

def update_conversion_rate_middleware_sync(make_request):
    def middleware(method, params)
        rate = params.get('rate', False)
        if rate:
            rate = sync_pull_conversion_rate(price)
            params['rate'] = rate

        return make_request(method, params)
```

After the function is expanded into the two variants, `pacro` will look through the ast for
anywhere `update_conversion_rate_middleware` is called and replace it with the appropriate 
generated function which in this case will depend on whether `make_request` is a coroutine
and if `update_conversion_rate_middleware` is being awaited.

One limitation is that where ever `update_conversion_rate_middleware` is called, 
it needs to be know if the `make_request` is a coroutine or a function before runtime.

`pacro` is a library of tools that generate python code by modifiying your code's ast. 

`pacro` is being developed to solve the challenge of code reuse with asynchronous/synchronous 
code, but it will eventually be extended to a general macro implementation.

# Do Not Use this Code

This is a pre-alpha release (meaning nothing is written yet).
Nothing works and every change may be breaking!
