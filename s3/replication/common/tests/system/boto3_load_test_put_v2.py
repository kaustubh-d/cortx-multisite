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

import os
import sys
import boto3
import threading
from config import Config
from object_generator import GlobalTestDataBlock
from object_generator import FixedObjectDataGenerator
from s3replicationcommon.log import setup_logger
from s3replicationcommon.timer import Timer


def upload_object(logger, work_item):
    logger.debug("upload_object()")

    # data = GlobalTestDataBlock.create(work_item.object_size)
    # md5 = GlobalTestDataBlock.get_md5()
    gen = FixedObjectDataGenerator(logger, work_item.object_name, work_item.object_size)
    data = gen.get_full_data()

    logger.info("Starting upload for object {}".format(work_item.object_name))
    work_item.status = "failed"

    timer = Timer()
    timer.start()
    session = boto3.session.Session()

    client = session.client("s3", use_ssl=False,
                            endpoint_url=work_item.endpoint,
                            aws_access_key_id=work_item.access_key,
                            aws_secret_access_key=work_item.secret_key)

    response = client.put_object(
        Body=data,
        ContentLength=work_item.object_size,
        Bucket=work_item.bucket_name,
        Key=work_item.object_name)
    timer.stop()

    md5 = gen.get_md5()
    returned_etag = response['ETag'].strip('"')
    assert returned_etag == md5, "Upload failed for object " + \
        work_item.object_name + \
        "\nReturned Etag: {}".format(returned_etag) + \
        "\nUploaded data md5 {}".format(md5)

    work_item.status = "success"
    logger.info("Completed upload for object {}".format(work_item.object_name))

    work_item.time_for_upload = timer.elapsed_time_ms()


class WorkItem:
    def __init__(self, bucket_name, object_name, object_size,
                 endpoint, access_key, secret_key):
        self.bucket_name = bucket_name
        self.object_name = object_name
        self.object_size = object_size
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.status = None
        self.time_for_upload = None


def main():

    config = Config()

    bucket_name = "boto3bucket"
    total_count = 100  # Number of objects to upload.
    object_size = 4096  # Bytes.

    # Setup logging and get logger
    log_config_file = os.path.join(os.path.dirname(__file__),
                                   'config', 'logger_config.yaml')

    print("Using log config {}".format(log_config_file))
    logger = setup_logger('client_tests', log_config_file)
    if logger is None:
        print("Failed to configure logging.\n")
        sys.exit(-1)

    # Init Global.
    GlobalTestDataBlock.create(object_size)

    # Create resources for each thread.
    work_items = []
    for i in range(total_count):
        # Generate object name
        object_name = "test_object_" + str(i) + "_sz" + str(object_size)
        work_item = WorkItem(bucket_name, object_name, object_size,
                             config.endpoint, config.access_key, config.secret_key)
        work_items.append(work_item)

    # Start threads to upload objects.
    request_threads = []
    for i in range(total_count):

        t = threading.Thread(
            target=upload_object, args=(
                logger, work_items[i],))
        request_threads.append(t)
        t.start()

    # Wait for threads to complete.
    total_time_ms = 0
    failed_count = 0
    for i in range(total_count):
        request_threads[i].join()
        if work_items[i].status == "success":
            total_time_ms += work_items[i].time_for_upload
        else:
            failed_count += 1

    logger.info("Total time to upload {} objects = {} ms.".format(
        total_count - failed_count, total_time_ms))
    logger.info("Avg time per upload = {} ms.".format(
        total_time_ms / total_count - failed_count))


# Run the test
main()
