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

import aiohttp
import asyncio
import os
import sys
from config import Config
from s3replicationcommon.aws_v4_signer import AWSV4Signer


async def data_generator(object_sz, chunk_size):
    total_chunks = int(object_sz / chunk_size)
    for _ in range(0, total_chunks):
        yield os.urandom(chunk_size)


async def main():
    async with aiohttp.ClientSession() as session:

        config = Config()

        bucket_name = config.source_bucket_name
        object_name = config.object_name_prefix + "test"

        request_uri = AWSV4Signer.fmt_s3_request_uri(bucket_name, object_name)
        query_params = ""
        body = ""

        headers = AWSV4Signer(
            config.endpoint,
            config.s3_service_name,
            config.s3_region,
            config.access_key,
            config.secret_key).prepare_signed_header(
            'PUT',
            request_uri,
            query_params,
            body)

        if (headers['Authorization'] is None):
            print("Failed to generate v4 signature")
            sys.exit(-1)

        headers["Content-Length"] = str(config.object_size)

        print('PUT on {} for object size {} bytes.'.format(
            config.endpoint + request_uri, config.object_size))
        async with session.put(config.endpoint + request_uri,
                               headers=headers,
                               data=data_generator(
                                   config.object_size,
                                   config.transfer_chunk_size)) as resp:
            print(resp.status)
            print(await resp.text())


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
