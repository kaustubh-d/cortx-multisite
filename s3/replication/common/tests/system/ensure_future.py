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
from config import Config

async def async_fun():
    print("started...")

async def main():

    config = Config()

    total_count = 100  # Number of objects to upload.

    put_task_list = []
    for i in range(total_count):
        if i % 10 == 0:
            print("asyncio.sleep")
            await asyncio.sleep(1)
        # task = asyncio.ensure_future(async_fun())
        task = asyncio.create_task(async_fun())
        put_task_list.append(task)
        # put_task_list.append(async_fun())
    
    print("gather...")
    await asyncio.gather(*put_task_list)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
