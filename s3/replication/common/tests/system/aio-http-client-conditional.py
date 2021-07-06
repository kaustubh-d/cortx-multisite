#!/usr/bin/env python3

import asyncio
import aiohttp
import time
import os
import sys

class TestData:
    data = None

    @classmethod
    def create(cls):
        if cls.data is None:
            cls.data = os.urandom(4096)
        return cls.data

class ReducingCounter(object):
    def __init__(self, max_val):
        self.count = max_val

class TotalRequestTime(object):
    def __init__(self) -> None:
        self.elapsed_time_ms = 0


async def async_put_api(session, uri, counter=None,
                        all_tasks_processed=None, total_timer=None):
    start_time = time.perf_counter()

    resp = await session.put(uri, data=TestData.create())

    end_time = time.perf_counter()
    elapsed_time_ms = int(round((end_time - start_time) * 1000))
    print("Time for request number {} = {} ms".format(counter.count, elapsed_time_ms))

    assert resp.status == 200

    # Add time to total timer.
    total_timer.elapsed_time_ms += elapsed_time_ms
    if counter is not None:
        counter.count -= 1
        if counter.count == 0:
            if all_tasks_processed is not None:
                async with all_tasks_processed:
                    all_tasks_processed.notify()

    return

def print_report(test_title, total_count, total_time_ms):
    print("{}".format(test_title))
    print("Total time for {} requests = {} ms.".format(
        total_count, total_time_ms))
    print("Avg time per request = {} ms.\n\n".format(
        total_time_ms / total_count))
    print("----------------------------------------")

# Test case 1: Runs each request in sequence and runs fastest.
async def test_case_1(short_label, total_count):
    print("Params: total_count {}".format(total_count))
    client_session = aiohttp.ClientSession()

    # total_time_ms = 0
    total_timer = TotalRequestTime()
    for i in range(total_count):
        resource_name = "test_" + str(i)
        uri = "http://localhost/resource/{}".format(resource_name)
       
        resp = await async_put_api(client_session, uri, total_timer=total_timer)
        # total_time_ms += resp["elapsed_time"]

    print_report("{}: Sequential async requests.".format(short_label),
                 total_count, total_timer.elapsed_time_ms)

    await client_session.close()

# Test case 2: Runs all requests in parallel and runs slowest.
async def test_case_2(short_label, total_count, max_conn):
    print("Params: total_count {}, max_conn {}".format(
        total_count, max_conn))
    connector = aiohttp.TCPConnector(limit=max_conn)
    client_session = aiohttp.ClientSession(connector=connector)

    # total_time_ms = 0
    task_list = []
    # Each task on completion decrements the counter.
    counter = ReducingCounter(total_count)
    total_timer = TotalRequestTime()
    # condition signaled when counter becomes zero after all jobs processed.
    all_tasks_processed = asyncio.Condition()
    for i in range(total_count):
        resource_name = "test_" + str(i)
        uri = "http://localhost/resource/{}".format(resource_name)
       
        task = asyncio.ensure_future(async_put_api(
            client_session, uri, counter, all_tasks_processed, total_timer))
        task_list.append(task)

    async with all_tasks_processed:
        await all_tasks_processed.wait()
    # await all_tasks_processed.release()

    # responses = await asyncio.gather(*task_list)

    # for response in responses:
    #     total_time_ms += response["elapsed_time"]

    print_report("{}: Parallel async requests.".format(short_label),
                 total_count, total_timer.elapsed_time_ms)

    await client_session.close()

# Test case 3: Runs few requests in parallel and runs better compared to Case 2.
async def test_case_3(short_label, total_count, max_conn, group_size):
    print("Params: total_count {}, max_conn {}, group_size {}".\
        format(total_count, max_conn, group_size))

    connector = aiohttp.TCPConnector(limit=max_conn)
    client_session = aiohttp.ClientSession(connector=connector)

    # total_time_ms = 0
    total_timer = TotalRequestTime()
    index = 0
    for i in range(total_count):
        task_list = []
        # Each task on completion decrements the counter.
        counter = ReducingCounter(group_size)
        # condition signaled when counter becomes zero after all jobs processed.
        all_tasks_processed = asyncio.Condition()
        # Launch group_size count of requests in parallel.
        for j in range(group_size):
            index += 1
            resource_name = "test_" + str(index)
            uri = "http://localhost/resource/{}".format(resource_name)
          
            task = asyncio.ensure_future(async_put_api(
                client_session, uri, counter, all_tasks_processed, total_timer))
            task_list.append(task)

        # responses = await asyncio.gather(*task_list)
        async with all_tasks_processed:
            await all_tasks_processed.wait()

        # for response in responses:
        #     total_time_ms += response["elapsed_time"]

    print_report("{}: Parallel grouped async requests.".format(short_label),
                 total_count, total_timer.elapsed_time_ms)

    await client_session.close()

async def main():

    TestData.create()

    # Sequential requests.
    # await test_case_1("seq-1", total_count=100)

    # Parallel requests - all
    await test_case_2("parallel-1", total_count=100, max_conn=100)
    await test_case_2("parallel-2", total_count=100, max_conn=10)
    await test_case_2("parallel-3", total_count=100, max_conn=1)

    # Parallel requests - grouped
    await test_case_3("grouped-1", total_count=100, max_conn=100, group_size=10)
    await test_case_3("grouped-2", total_count=100, max_conn=100, group_size=5)
    await test_case_3("grouped-3", total_count=100, max_conn=100, group_size=1)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
