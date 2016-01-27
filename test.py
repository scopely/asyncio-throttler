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
