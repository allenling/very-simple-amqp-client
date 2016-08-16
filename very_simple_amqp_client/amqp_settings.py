# coding=utf-8
from __future__ import unicode_literals
from __future__ import absolute_import

major = 0
minor = 9
revision = 1

MAX_FRAME_SIZE = 131072

PROTOCOL_HEADER_FRAME_TYPE = 0

METHOD_FRAME_TYPE = 1

CONTENT_HEADER_FRAME_TYPE = 2

BODY_FRAME_TYPE = 3

HEADRTBEAT_FRAME_TYPE = 8

FRAME_HEADER_SIZE = 7

FRAME_END_SIZE = 1

FRAME_END_MARK = chr(206)
