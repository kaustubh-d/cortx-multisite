#!/usr/bin/env python3

import asyncio
import aiohttp
from typing import Counter
from aiohttp import web
import time
import os

# Route table declaration
routes = web.RouteTableDef()


@routes.get('/')  # noqa: E302
async def get_handler(request):
    print('API: GET /')
    await start_requests(app)
    return web.json_response(status=200)


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


async def async_put_api(session, uri, counter=None, total_timer=None):
    start_time = time.perf_counter()

    resp = await session.put(uri, data=TestData.create())

    end_time = time.perf_counter()
    elapsed_time_ms = int(round((end_time - start_time) * 1000))
    #print("Time for request number {} = {} ms".format(counter.count, elapsed_time_ms))

    assert resp.status == 200

    # Add time to total timer.
    total_timer.elapsed_time_ms += elapsed_time_ms
    if counter is not None:
        counter.count -= 1
        if counter.count == 0:
            print("All jobs done...")

    return

def print_report(test_title, total_count, total_time_ms):
    print("{}".format(test_title))
    print("Total time for {} requests = {} ms.".format(
        total_count, total_time_ms))
    print("Avg time per request = {} ms.\n\n".format(
        total_time_ms / total_count))
    print("----------------------------------------")

async def start_requests(app):
    print("Starting requests...")
    total_count = 100
    max_conn = 100
    app["total_count"] = total_count

    connector = aiohttp.TCPConnector(limit=max_conn)
    client_session = aiohttp.ClientSession(connector=connector)
    app["client_session"] = client_session

    counter = ReducingCounter(total_count)
    total_timer = TotalRequestTime()
    app["total_timer"] = total_timer

    for i in range(total_count):
        resource_name = "test_" + str(i)
        uri = "http://localhost/resource/{}".format(resource_name)
        asyncio.ensure_future(async_put_api(client_session, uri, counter, total_timer))
    

async def on_startup(app):
    print("Starting server...")

async def on_shutdown(app):
    print("Stopping server")
    await app["client_session"].close()
    # Print results
    print_report("test", app["total_count"], app["total_timer"].elapsed_time_ms)

if __name__ == '__main__':
    app = web.Application()

    # Setup application routes.
    app.add_routes(routes)

    # Setup startup/shutdown handlers
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Start the REST server.
    web.run_app(app, host="0.0.0.0", port="81")
