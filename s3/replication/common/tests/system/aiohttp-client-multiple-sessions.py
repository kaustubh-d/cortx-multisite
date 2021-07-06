#!/usr/bin/env python3

import asyncio
import aiohttp
import aiodns
import time
import os

class TestData:
    data = None

    @classmethod
    def create(cls):
        if cls.data is None:
            cls.data = os.urandom(4096)
        return cls.data

async def async_put_api(session, uri):
    start_time = time.perf_counter()

    resp = await session.put(uri, data=TestData.create())

    end_time = time.perf_counter()
    elapsed_time_ms = int(round((end_time - start_time) * 1000))

    assert resp.status == 200

    return {"elapsed_time": elapsed_time_ms}

def print_report(test_title, total_count, total_time_ms):
    print("{}".format(test_title))
    print("Total time for {} requests = {} ms.".format(
        total_count, total_time_ms))
    print("Avg time per request = {} ms.\n\n".format(
        total_time_ms / total_count))
    print("----------------------------------------")

# Test case 2: Runs all requests in parallel and runs slowest.
async def test_case_2(short_label, total_count):
    print("Params: total_count {}".format(
        total_count))

    total_time_ms = 0
    task_list = []
    sessions = []
    for i in range(total_count):
        connector = aiohttp.TCPConnector()
        client_session = aiohttp.ClientSession(connector=connector)
        sessions.append(client_session)

        resource_name = "test_" + str(i)
        uri = "http://127.0.0.1/source/{}".format(resource_name)
       
        task = asyncio.ensure_future(async_put_api(client_session, uri))
        task_list.append(task)

    responses = await asyncio.gather(*task_list)

    for response in responses:
        total_time_ms += response["elapsed_time"]

    print_report("{}: Parallel async requests.".format(short_label),
                 total_count, total_time_ms)

    for i in range(total_count):
        await sessions[i].close()

async def main():

    TestData.create()

    # Parallel requests - all
    await test_case_2("parallel-1", total_count=1000)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
