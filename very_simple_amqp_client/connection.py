# coding=utf-8
from __future__ import unicode_literals
from __future__ import absolute_import
import socket
import select

from . import amqp_settings

from .channel import Channel
from . import frame


class AmqpUrlParser(object):

    def __init__(self, url):
        self.url = url
        self.protocol, rest = self.url.split('://')
        if self.protocol.lower() != 'amqp':
            raise StandardError('not amqp protocol')
        user_and_pwd, address = rest.split('@')
        self.user, self.password = user_and_pwd.split(':')
        self.host, self.port = address.split(':')
        self.port, self.vhost = self.port.split('/')
        self.port = int(self.port)
        if self.vhost == '':
            self.vhost = '/'


class Connection(object):

    def __init__(self, amqp_url):
        self.amqp_config = AmqpUrlParser(amqp_url)
        self.channel_number = 1
        self.callbacks = {}
        self.channel = None

    def initial_socket(self, address):
        self.socket = socket.socket(*address[:3])
        self.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.socket.settimeout(1)
        self.socket.connect(address[4])

    def connect(self, on_open_callback):
        addresses = socket.getaddrinfo(self.amqp_config.host, self.amqp_config.port, socket.AF_UNSPEC, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        for address in addresses:
            self.initial_socket(address)
            break
        self.callbacks['on_connection_open_ok'] = on_open_callback
        self.epoll = select.epoll()
        self.epoll.register(self.socket.fileno(), select.EPOLLIN | select.EPOLLERR)
        print self.socket.fileno()
        self.send_protocol_header()

    def send_frame(self, raw_data):
        # send amqp frame
        self.socket.send(raw_data)

    def channel(self):
        self.channel = Channel(self, self.channel_number)
        return self.channel

    def send_protocol_header(self):
        # first of all, send AMQP header
        protocol_header_frame = frame.get_protocol_header_frame()
        self.send_frame(protocol_header_frame.pack())

    def on_start(self):
        # recv start, and send start_ok
        pass

    def on_tune(self):
        # recv tune, and send tune_ok, and send connection_open
        pass

    def on_connection_open_ok(self):
        self.callbacks['on_connection_open_ok'](self)

    def read(self):
        data = self.socket.recv(amqp_settings.MAX_FRAME_SIZE)
        if not data or data == 0:
            print 'recv empty data'
            return
        frame_object = frame.get_frame_object_from_raw_frame(data)
        if frame_object.channel > 0:
            self.channel.process_frame(frame_object)
        else:
            self.process_frame(frame_object)

    def send_connecton_start(self):
        connection_start_ok_frame = frame.METHOD_NAMES['Connection.Start-Ok'](0)
        self.send_frame(connection_start_ok_frame.pack(self.amqp_config.user, self.amqp_config.password))

    def process_frame(self, frame_object):
        if frame_object.frame_type == amqp_settings.METHOD_FRAME_TYPE:
            if frame_object.method_id == frame.METHOD_NAMES['Connection.Start'].method_id:
                # send start ok
                self.send_connecton_start()

    def handle_event(self, fd, event):
        if event == select.EPOLLERR:
            self.handle_error(fd, event)
        elif event == select.EPOLLIN:
            self.read()
        else:
            print 'invalid event %s in fd %s' % (event, fd)

    def handle_error(self, fd, event):
        pass

    def start(self):
        while True:
            events = self.epoll.poll(1)
            for fd, event in events:
                print fd, event
                if fd == 0:
                    continue
                self.handle_event(fd, event)
