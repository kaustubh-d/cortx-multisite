#!/usr/bin/env python3

import os
import requests
import threading
import time

class TestData:
    data = None

    @classmethod
    def create(cls):
        if cls.data is None:
            cls.data = os.urandom(1024)
        return cls.data

class WorkItem:
    def __init__(self, uri, session):
        self.uri = uri
        self.session = session
        self.status = None
        self.elapsed_time_ms = None

def thread_func_put_api(work_item):
    start_time = time.perf_counter()

    resp = work_item.session.put(work_item.uri, data=TestData.create())

    end_time = time.perf_counter()

    work_item.elapsed_time_ms = int(round((end_time - start_time) * 1000))
    work_item.status = resp.status_code

    assert resp.status_code == 200

    return

def print_report(test_title, total_count, total_time_ms):
    print("{}".format(test_title))
    print("Total time for {} requests = {} ms.".format(
        total_count, total_time_ms))
    print("Avg time per request = {} ms.\n\n".format(
        total_time_ms / total_count))
    print("----------------------------------------")

# Test case 1: Runs each request in sequence.
def test_case_1(short_label, total_count):
    print("Params: total_count {}".format(total_count))
    client_session = requests.Session()

    total_time_ms = 0
    for i in range(total_count):
        resource_name = "test_" + str(i)
        uri = "http://localhost/{}".format(resource_name)

        work = WorkItem(uri, client_session)
        thread_func_put_api(work)

        total_time_ms += work.elapsed_time_ms

    print_report("{}: Sequential requests.".format(short_label),
                 total_count, total_time_ms)

# Test case 2: Runs all requests in parallel, 1 request per thread.
def test_case_2(short_label, total_count):
    print("Params: total_count {}, threads_count {}".format(
        total_count, total_count))
    client_session = requests.Session()

    # Start threads to upload objects.
    request_threads = []
    work_items = []
    for i in range(total_count):
        resource_name = "test_" + str(i)
        uri = "http://localhost/{}".format(resource_name)

        work = WorkItem(uri, client_session)
        work_items.append(work)

        t = threading.Thread(
            target=thread_func_put_api, args=(work,))
        request_threads.append(t)
        t.start()

    # Wait for threads to complete.
    total_time_ms = 0
    for i in range(total_count):
        request_threads[i].join()
        assert work_items[i].status == 200
        total_time_ms += work_items[i].elapsed_time_ms

    print_report("{}: Parallel threaded requests.".format(short_label),
                 total_count, total_time_ms)

def main():

    TestData.create()

    # Sequential requests.
    test_case_1("seq-1", total_count=100)

    # Parallel requests with threads - all
    test_case_2("parallel-1", total_count=100)


if __name__ == '__main__':
    main()