# coding=utf-8
from __future__ import unicode_literals
from __future__ import absolute_import
import struct

import pika

from . import amqp_settings


class AMQPFrame(object):
    frame_type = None
    channel = None
    size = None
    payload = None

    def pack(self):
        pass

    def unpack(self, raw_frame, size):
        pass


class ProtocolHeaderFrame(AMQPFrame):
    frame_type = amqp_settings.PROTOCOL_HEADER_FRAME_TYPE

    def pack(self):
        return b'AMQP' + struct.pack('BBBB', 0, amqp_settings.major, amqp_settings.minor, amqp_settings.revision)


class MethodFrame(AMQPFrame):
    frame_type = amqp_settings.METHOD_FRAME_TYPE
    class_id = None
    method_id = None
    name = None

    def __init__(self, channel):
        self.channel = channel

    def pack(self):
        pass

    def unpack(self, raw_frame, size):
        pass


class ConnectionStart(MethodFrame):
    class_id = 10
    method_id = 10
    version_major = None
    version_minor = None
    server_properties = None
    mechanisms = None
    locales = None
    name = 'Connection.Start'

    def unpack(self, raw_frame, size):
        self.size = size
        self.version_major, self.version_minor = struct.unpack('B', raw_frame[11]), struct.unpack('B', raw_frame[12])


class ConnectionStartOk(MethodFrame):
    class_id = 10
    method_id = 11
    name = 'Connection.Start-Ok'
    client_properties = {'product': 'very simple amqp client', 'version': '0.1.0', 'Platform': 'Ubuntu 14.04'}
    mechanism = 'PLAIN'
    response = None
    locale = 'en_US'

    def pack(self, user, password):
        pieces = []
        pika.data.encode_table(pieces, self.client_properties)
        pika.data.encode_short_string(pieces, self.mechanism)
        self.response = b'\0' + user.encode('utf-8') + b'\0' + password.encode('utf-8')
        pieces.append(struct.pack('>I', len(self.response)))
        pieces.append(self.response)
        pika.data.encode_short_string(pieces, self.locale.encode('utf-8'))
        pieces.insert(0, struct.pack('>BB', 00, self.method_id))
        pieces.insert(0, struct.pack('>BB', 00, self.class_id))
        payload = b''.join(pieces)
        return struct.pack('>BHI', self.frame_type, self.channel, len(payload)) + payload + amqp_settings.FRAME_END_MARK


class ContentHeaderFrame(AMQPFrame):
    frame_type = amqp_settings.CONTENT_HEADER_FRAME_TYPE
    weight = None
    body_size = None
    property_flag = None
    property_list = None


class BodyFrame(AMQPFrame):
    frame_type = amqp_settings.BODY_FRAME_TYPE


class HeartbeatFrame(AMQPFrame):
    frame_type = amqp_settings.HEADRTBEAT_FRAME_TYPE


METHOD_NAMES = {'Connection.Start': ConnectionStart,
                'Connection.Start-Ok': ConnectionStartOk}


METHOD_IDS = {}

for i in METHOD_NAMES:
    METHOD_IDS['%s_%s' % (METHOD_NAMES[i].class_id, METHOD_NAMES[i].method_id)] = METHOD_NAMES[i]


def get_protocol_header_frame():
    return ProtocolHeaderFrame()


def get_frame_object_from_raw_frame(raw_frame):
    # is a protocol header frame
    if raw_frame[0:4] == b'AMQP':
        major, minor, revision = struct.unpack_from('BBB', raw_frame, 5)
        if (major, minor, revision) != (amqp_settings.major, amqp_settings.minor, amqp_settings.revision):
            raise StandardError('amqp version does not match!')
        return ProtocolHeaderFrame()

    frame_type, channel_number, payload_size = struct.unpack('>BHL', raw_frame[0:amqp_settings.FRAME_HEADER_SIZE])
    if raw_frame[-1] != amqp_settings.FRAME_END_MARK:
        raise StandardError('invalid frame end mark %s' % raw_frame[-1])

    payload = raw_frame[amqp_settings.FRAME_HEADER_SIZE:-1]

    if frame_type == amqp_settings.METHOD_FRAME_TYPE:
        class_id, method_id = struct.unpack('B', payload[1:2])[0], struct.unpack('B', payload[3:4])[0]
        method_frame = METHOD_IDS['%s_%s' % (class_id, method_id)](channel_number)
        method_frame.unpack(raw_frame, payload_size)
        return method_frame
    elif frame_type == amqp_settings.CONTENT_HEADER_FRAME_TYPE:
        return
    elif frame_type == amqp_settings.BODY_FRAME_TYPE:
        return
    else:
        raise StandardError('unsupported frame type')
