Asyncio Throttler
=================

``asyncio`` and ``async``/``await`` are pretty awesome tools!
Asynchronous stuff! In Python! Without insanity!

Well, unfortunately given the nature of this style of programming it's
not bloody easy sometimes.

Well, this project provides at least one tool to help ya out in a
reasonably simple way.

*asyncio\_throttler* is a throttling system for Python 3.5+, designed
aiohttp throttling in mind but designed to be flexible enough to handle
most throttling and rate limiting needs.

Usage
-----

Well, get it:

::

    $ pyvenv env/
    $ . env/bin/activate
    $ pip install asyncio_throttler # Pin the damned version in setup.py
                                    # you bloody savage.

If you don't have Python 3.5, check out
`pyenv <https://github.com/yyuu/pyenv>`__ (not to be confused with
py\ **v**\ env), a Python version manager similar to rbenv.

If you really don't want pyenv, ``brew install python3`` will
non-destructively install Python 3.5+.

Anyways, here's the terrible usage example I wrote while developing the
thing. The code is well documented, concise, and hopefully easily
understandable by humans, but this should getcha started. I'll make
better docs, I promise. I gotta sleep at some point.

**WARNING: THIS WILL NEVER COMPLETE, THE THROTTLE ERROR WILL BOUNCE
AROUND FOREVER. ON PURPOSE. TO DEMONSTRATE THINGS DON'T GET LOST.
SERIOUSLY.**

.. code:: python

    """Dump test module I built while writing this thing. Need to make real tests,
    but whatcha gonna do ya got schedules and stuff amirite?

    """
    import logging
    import asyncio
    from asyncio_throttler import Throttler, ThrottleException

    # Demonstrates that windowing, throttling, and every other known feature
    # works, I think.
    if __name__ == '__main__':
        logger = logging.getLogger('testthrottler')
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        format_template = '%(asctime)s:%(name)s:%(levelname)s – %(message)s'
        handler.setFormatter(logging.Formatter(fmt=format_template,
                                               datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(handler)

        async def dummy_consumer(item):
            print("Item received:", item)
            await asyncio.sleep(2)

        import random
        async def dummy_task():
            logger.info("Executed")
            return await asyncio.sleep(1, random.randrange(1, 1000))

        async def bad_dummy_task():
            logger.info("Executed and gonna throw a throttle")
            raise ThrottleException(bad_dummy_task())

        loop = asyncio.get_event_loop()

        # roflcoptr
        todo_list = [dummy_task() for _ in range(1, 31)]
        todo_list.append(bad_dummy_task())
        todo_list = todo_list + [dummy_task() for _ in range(1, 31)]

        throttler = Throttler(
            todo_list,
            dummy_consumer,
            time_window=10,
            per_time_window=20,
            concurrency=5,
            log_handler=logging.StreamHandler(),
            log_level=logging.DEBUG,
            loop=loop
        )

        loop.run_until_complete(throttler.run())
        loop.close()

How's It Works
--------------

A Throttler is instantiated with a list of awaitables, an async
function, and numerous keyword arg knobs you adjust to suit your
purposes.

Inside are two ``asyncio.Queue`` objects, and one ``asyncio.LifoQueue``.

-  ``exceptions`` is a ``Queue`` for non-throttle exceptions we catch.
-  ``processed`` is a ``Queue`` for processed output. This is what your
   consumer will consume from.
-  ``todo`` is a ``LifoQueue`` that holds your unprocessed task list.
   It's initially fed from a ``reverse`` of the list you pass to
   ``Throttler``, which is fast and an iterator. It's ``LIFO`` just so
   we can pop throttled items back into it at the front.

Several internal functions are composed to create an async producer and
consumer loop where items are processed as fast as possible given the
restrictions imposed at ``Throttler`` instantiation. It'll backoff
``time_window`` when throttled, only execute ``concurrency`` of your
tasks at a time, and will wait ``time_window`` after triggering the
processing of ``per_time_window`` items.

That oughta cover a few cases...

Anyways, the async ``consumer_fn`` you pass in will be executed as
results become available, immediately, for writing to disk or somethin'.

Notes
-----

This was painful.
