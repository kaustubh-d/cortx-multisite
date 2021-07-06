#!/usr/bin/env python3

import asyncio
import aiohttp
import time
import os

def print_report(total_count, total_time_ms):
    print("Total time for {} requests = {} ms.".format(
        total_count, total_time_ms))
    print("Avg time per request = {} ms.\n".format(
        total_time_ms / total_count))
    print("-----------------------------------------\n")

async def async_put_api(session):
    start_time = time.perf_counter()

    resp = await session.put("http://localhost/hello", data="Hello world!")

    end_time = time.perf_counter()
    elapsed_time_ms = int(round((end_time - start_time) * 1000))

    assert resp.status == 200

    return {"elapsed_time": elapsed_time_ms}

# Test case 1: Runs each request in sequence.
async def test_case_seq_reqs(total_count):
    print("\nSequential Requests:\nParams: total_count {}".format(total_count))
    client_session = aiohttp.ClientSession()

    total_time_ms = 0
    for i in range(total_count):
        resp = await async_put_api(client_session)
        total_time_ms += resp["elapsed_time"]

    print_report(total_count, total_time_ms)

    await client_session.close()

# Test case 2: Runs all requests in parallel and runs slowest.
async def test_case_parallel(total_count, max_conn):
    print("\nParallel Requests:\nParams: total_count {}, max_conn {}".format(
        total_count, max_conn))
    connector = aiohttp.TCPConnector(limit=max_conn, limit_per_host=max_conn)
    client_session = aiohttp.ClientSession(connector=connector)

    total_time_ms = 0
    task_list = []
    for i in range(total_count):
        task = asyncio.ensure_future(async_put_api(client_session))
        task_list.append(task)

    responses = await asyncio.gather(*task_list)

    for response in responses:
        total_time_ms += response["elapsed_time"]

    print_report(total_count, total_time_ms)

    await client_session.close()

async def main():
    total_count = 100
    # Sequential requests.
    await test_case_seq_reqs(total_count=total_count)

    # Parallel requests - all
    await test_case_parallel(total_count=total_count, max_conn=100)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
