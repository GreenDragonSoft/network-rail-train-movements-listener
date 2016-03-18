#!/usr/bin/env python3

import json
import os
import time
import uuid

import boto3
import stomp

from logger import LOG

from batcher import batcher


LOG_EVERY_N_MESSAGES = 1000


class UploadStompMessagesToAmazonSQS(object):
    def __init__(self, sqs_queue_url, region_name='eu-west-1'):
        self.sent_message_count = 0
        self.sent_bytes = 0

        self.sqs = boto3.resource('sqs', region_name)
        self.queue = self.sqs.Queue(sqs_queue_url)

    def on_error(self, headers, message):
        LOG.error("ERROR: {} {}".format(headers, message))

    def on_message(self, stomp_headers, json_encoded_messages):
        LOG.debug('STOMP headers {}'.format(stomp_headers))

        try:
            messages = json.loads(json_encoded_messages)
        except ValueError as e:
            LOG.error('Failed to decode {} bytes as JSON: {}'.format(
                len(json_encoded_messages), json_encoded_messages))
            LOG.exception(e)
            return

        try:
            self._handle_multiple_messages(messages)
        except Exception as e:
            LOG.exception(e)
            return

    def _handle_multiple_messages(self, messages):
        """
        Train movement message comprises a `header` and a `body`. The `header`
        http://nrodwiki.rockshore.net/index.php/Train_Movement

        """
        def send_batch(sqs_entries):
            # http://boto3.readthedocs.org/en/latest/reference/services/sqs.html#SQS.Queue.sendentries
            result = self.queue.send_messages(Entries=sqs_entries)

            if len(result['Successful']) != len(sqs_entries):
                LOG.error('Some messages failed to send to SQS: {}'.format(
                    result))

        with batcher(send_batch, batch_size=10) as b:
            for raw_message in messages:
                message_id = str(uuid.uuid4())

                pretty_message = json.dumps(raw_message, indent=4)
                LOG.debug('Sending to queue with id {}: {}'.format(
                    message_id, pretty_message))

                b.push({
                    'Id': message_id,
                    'MessageBody': pretty_message
                })

                self.increment_message_counter(len(raw_message))

    def increment_message_counter(self, num_bytes):
        self.sent_message_count += 1
        self.sent_bytes += num_bytes

        if self.sent_message_count % LOG_EVERY_N_MESSAGES == 0:
            LOG.info('Sent {} messages, ~{:.3f} MB'.format(
                self.sent_message_count,
                self.sent_bytes / (1024 * 1024)))


def main():
    username = os.environ['NR_DATAFEEDS_USERNAME']
    password = os.environ['NR_DATAFEEDS_PASSWORD']

    # See http://nrodwiki.rockshore.net/index.php/Train_Movements
    datafeeds_hostname = 'datafeeds.networkrail.co.uk'
    datafeeds_channel = 'TRAIN_MVT_ALL_TOC'

    handler = UploadStompMessagesToAmazonSQS(os.environ['AWS_SQS_QUEUE_URL'])

    conn = create_data_feed_connection(
        datafeeds_hostname, username, password, datafeeds_channel, handler)

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            LOG.info("Keyboard interrupt, quitting.")
            break

    conn.disconnect()


def create_data_feed_connection(hostname, username, password, channel,
                                handler):
    conn = stomp.Connection(host_and_ports=[(hostname, 61618)])

    conn.set_listener('mylistener', handler)
    conn.start()
    conn.connect(username=username, passcode=password)

    conn.subscribe(destination='/topic/{}'.format(channel), id=1, ack='auto')
    return conn

if __name__ == '__main__':
    main()
