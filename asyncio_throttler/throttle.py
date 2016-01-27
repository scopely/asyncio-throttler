"""Super flexible throttling tools."""
import logging
import asyncio


class ThrottleException(Exception):
    """Throttle exception class, specialized for holding a replacement task
    to pop back in the queue if the task gets throttled.

    """
    def __init__(self, task):
        self.task = task

    def __str__(self):
        return repr(self.task)


class Throttler(object):
    """A flexible throttler class.

    Takes a list of asyncio tasks, `todo_list`, and an async consumer function
    that will receive items as they are processed and complete (not in order).

    Only executes triggers execution of `per_time_window` tasks, sleeping for
    `time_window` after triggering each batch.

    `concurrency` sets the max number of tasks that can run at any given time,
    which is particularly useful for http requests, not bombing servers and
    such.

    This class has logging built in, and it can be controlled via the
    `log_level` and `log_handler` args. By default level is `logging.INFO` and
    handler is `logging.NullHandler` so we're quiet by default. You probably
    want to use a `StreamHandler` in your application.

    Like every other asyncio tool in the universe, we also take an optional
    `loop` argument and otherwise use the default event loop.

    For dealing with throttling, your input tasks should raise a
    `ThrottleException`, instantiating it (or a subclass) with a new task
    instance so it can be thrown back into the queue and retried after the
    set timeout period.

    """
    def __init__(self, todo_list, consumer_fn, *,
                 time_window=60,
                 per_time_window=100,
                 concurrency=5,
                 log_level=logging.INFO,
                 log_handler=logging.NullHandler(),
                 loop=None):
        self.time_window = time_window
        self.consumer_fn = consumer_fn
        self.per_time_window = per_time_window

        # Setup logging! It takes a moment!
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)
        handler = log_handler or logging.NullHandler()
        format_template = '%(asctime)s:%(name)s:%(levelname)s – %(message)s'
        handler.setFormatter(logging.Formatter(fmt=format_template,
                                               datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(handler)
        self.log = logger

        # Safety check.
        todo_len = len(todo_list)
        if per_time_window >= todo_len:
            raise ValueError(("per_time_window should be less than the length "
                              "of todo_list. Not see much point in throttling "
                              "if there's no actual throttling."))

        # Get our event loop.
        loop = loop or asyncio.get_event_loop()
        self.loop = loop

        # Set up our queues. TODO: May need to use a different loop?
        self.processed = asyncio.Queue(todo_len, loop=loop)
        self.todo = asyncio.LifoQueue(todo_len, loop=loop)

        # Populate tasks. The canonical original tasks.
        for task in reversed(todo_list):
            self.todo.put_nowait(task)

        # Throttled processing setup.
        self.exceptions = asyncio.Queue(loop=loop)
        self.throttler = asyncio.Semaphore(concurrency, loop=loop)
        self._finished = asyncio.Event(loop=loop)

    async def _get_one(self):
        """Helper function to retrieve one todo item."""
        if not self.todo.empty():
            item = await self.todo.get()
            self.todo.task_done()
            return item

    async def _process_one(self, item):
        """Helper called for each item in a work set. Just throttles
        and returns the awaited item.

        """
        async with self.throttler:
            return await item

    async def _populate(self):
        """Main processing loop. Runs until all unfinished tasks are
        processed. Sleeps between batches and constantly populates the
        processed queue with task results.

        """
        self.log.info("Starting producer")
        while not self._finished.is_set():
            pending = []
            for _ in range(1, self.per_time_window + 1):
                if not self._finished.is_set():
                    item = await self._get_one()
                    if item:
                        pending.append(item)

            tasks = [self._process_one(task) for task in pending]

            self.log.info("Processing {} tasks".format(len(tasks)))
            for task in asyncio.as_completed(tasks, loop=self.loop):
                try:
                    result = await task
                    await self.processed.put(result)
                except Exception as e:
                    print("Caught exception", e)
                    print("Task is", task)
                    if isinstance(e, ThrottleException):
                        await self.todo.put(e.task)
                        self.log.warning(
                            ("We got throttled! Backing "
                             "off for {} seconds").format(self.time_window))
                        await asyncio.sleep(self.time_window, loop=self.loop)
                    else:
                        self.log.error(
                            ("Got an exception that wasn't a throttle. "
                             "Storing it in the exceptions queue."))
                        await self.exceptions.put(e)

            # Mark finished late in the game because the above code can
            # potentially pop an item back into the queue due to throttling.
            if self.todo.empty():
                self._finished.set()

            if not self._finished.is_set():
                self.log.info("Finished processing task set")
                self.log.info("{} items remaining in todo queue".format(
                    self.todo.qsize()))
                self.log.info(
                    "Sleeping for {} seconds".format(self.time_window))
                await asyncio.sleep(self.time_window)
            else:
                self.log.info("Done processing all tasks")

    async def _consume_processed(self):
        """Main consumer loop. Just runs `consumer_fn` on each processed
        task until all tasks are finished.

        """
        self.log.info("Starting consumer")
        while not self.processed.empty() or not self._finished.is_set():
            await self.consumer_fn(await self.processed.get())
            self.processed.task_done()

    async def run(self):
        """Trigger the throttler, starting the consumer and producer. Waits
        until both are completed.

        """
        producer = asyncio.ensure_future(self._populate())
        consumer = asyncio.ensure_future(self._consume_processed())

        done, _ = await asyncio.wait([producer, consumer],
                                     return_when=asyncio.ALL_COMPLETED)
        return done
