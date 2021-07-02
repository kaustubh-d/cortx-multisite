#!/usr/bin/env python3

#
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import asyncio
import aiohttp
from config import Config
import sys
from object_generator import GlobalTestDataBlock
from s3replicationcommon.timer import Timer

async def async_put_object(session, uri, data, object_size):
    timer = Timer()
    http_status = None
    returned_etag = None
    print("Triggering async_put_object for {}".format(uri))
    timer.start()
    # try:
    #   async with session.put(uri,
    #                          data=data
    #                         ) as resp:
    #       timer.stop()

    #       http_status = resp.status
    #       if resp.status == 200:
    #           returned_etag = resp.headers["Etag"].strip('"')
    # except aiohttp.client_exceptions.ClientConnectorError as e:
    #     timer.stop()
    resp = await session.put(uri, data=data)
    timer.stop()

    http_status = resp.status
    # print("Completed async_put_object with resp.headers {} ms".format(resp.headers))
    returned_etag = resp.headers["ETag"].strip('"')
    elapsed_time_ms = timer.elapsed_time_ms()
    print("Completed async_put_object for {} with {} ms".format(uri, elapsed_time_ms))

    return {"etag": returned_etag,
            "http_status": http_status,
            "elapsed_time": elapsed_time_ms
            }

async def main():

    config = Config()

    bucket_name = "sourcebucket"
    total_count = 100  # Number of objects to upload.
    object_size = 1024 * 1024  # Bytes.

    # Init Global.
    data = GlobalTestDataBlock.create(object_size)

    connector = aiohttp.TCPConnector(limit=1000,
        ttl_dns_cache=300)
    client_session = aiohttp.ClientSession(connector=connector)

    # Prepare for upload.
    total_groups = int(total_count / config.max_s3_connections)
    index = 0
    total_time_ms = 0

    for i in range(total_groups):
        put_task_list = []
        put_responses = []
        for i in range(config.max_s3_connections):
            index += 1
            # Generate object name
            object_name = "test_object_" + str(index) + "_sz" + str(object_size)
            uri = "http://s3.seagate.com/{}/{}".format(bucket_name, object_name)
          
            task = asyncio.ensure_future(async_put_object(client_session, uri, data, object_size))
            put_task_list.append(task)
            put_task_list.append(async_put_object(client_session, uri, data, object_size))

        put_responses = await asyncio.gather(*put_task_list)

        for response in put_responses:
            # Validate object uploaded successfully.
            assert response["http_status"] == 200
            print("PUT Object completed with http status: 200")

            upload_etag = response["etag"]
            data_md5 = GlobalTestDataBlock.get_md5()
            assert upload_etag == data_md5, \
                "PUT Etag = {} and Data MD5 = {}".format(upload_etag, data_md5)

            total_time_ms += response["elapsed_time"]

    print("Total time to upload {} objects = {} ms.".format(
        total_count, total_time_ms))
    print("Avg time per upload = {} ms.".format(
        total_time_ms / total_count))

    await client_session.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
