#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Junior Polegato
# Date..: 22 May 2013
# About.: Send USSD code to a serial modem port

import pdu
import serial
import sys
import time

_TIMEOUT = 30

def read_line(port, expected, print_line = False, timeout = _TIMEOUT):
    start = time.time()
    if isinstance(expected, (list, tuple)):
        expected = [str(x) for x in expected]
        max_size = max(len(x) for x in expected)
    else:
        expected = str(expected)
        max_size = len(expected)
    line = ''
    print 'Waiting for "%s" (%i)' % (str(expected), max_size)
    while (start + timeout > time.time() and
           (isinstance(expected, str) and line[:max_size] != expected or
            line[:max_size] not in expected)):
        line = ''
        d = 'x'
        while d and d != '\n':
            d = port.read(1)
            line += d
        line = line.rstrip()
        if print_line:
            print "%s? %s" % (str(expected), repr(line))
    return line

if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print "Run: %s ussd_command [port]" % sys.argv[0]
        print "Default port is /dev/ttyUSB0"
        sys.exit(1)

    if len(sys.argv) == 3:
        port = sys.argv[2]
    else:
        port = '/dev/ttyUSB0'

    cmd_pdu = pdu.text_to_pdu(sys.argv[1])
    print 'Sending "%s" ("%s") to "%s"...' % (sys.argv[1], cmd_pdu, port)

    port = serial.Serial(port, timeout = _TIMEOUT)

    port.write('at+cusd=1,"%s",15\r\n' % cmd_pdu)

    result = read_line(port, ('OK', 'ERROR'))
    if result != 'OK':
        print "Error while waiting for OK!"
        sys.exit(1)

    result = read_line(port, '+CUSD')
    if result[:5] != '+CUSD':
        print "Error while waiting for +CUSD!"
        sys.exit(1)

    response = pdu.pdu_to_text(result.split(',')[1].strip('"'))
    print 'Response:', response

    port.close()
