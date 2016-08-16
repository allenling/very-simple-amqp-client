# coding=utf-8
from __future__ import unicode_literals
from __future__ import absolute_import


class Channel(object):

    def __init__(self, connection, channel_number):
        self.connection = connection
        self.number = channel_number
        self.callbacks = {}
        self.consumer_tag = 'simple@%s' % self.number

    def open(self, on_open_ok_callback):
        # send channel_open
        self.callbacks['on_channel_open_ok'] = on_open_ok_callback

    def on_channel_open_ok(self):
        self.callbacks['on_channel_open_ok'](self)

    def declare_exchange(self, on_declare_exchange_ok_callback, exchange_name):
        # send exchange_declare
        self.exchange_name = exchange_name
        self.callbacks['on_exchange_declare_ok'] = on_declare_exchange_ok_callback

    def on_exchange_declare_ok(self):
        self.callbacks['on_exchange_declare_ok'](self, self.exchange_name)

    def declare_queue(self, on_queue_declare_ok_callback, queue_name):
        # send queue_clare
        self.queue_name = queue_name
        self.callbacks['on_queue_declare_ok'] = on_queue_declare_ok_callback

    def on_queue_declare_ok(self):
        self.callbacks['on_queue_declare_ok'](self, self.queue_name)

    def bind_queue_to_exchange(self, on_queue_bind_ok_callback):
        # send queue_bind
        self.callbacks['on_queue_bind_ok'] = on_queue_bind_ok_callback

    def on_queue_bind_ok(self):
        self.callbacks['on_queue_bind_ok'](self)

    def start_consume(self, process_callback):
        # send basic.consume
        self.callbacks['consume_message'] = process_callback

    def publish(self, message):
        # send message frame
        pass

    def process_frame(self, frame_obj):
        pass
