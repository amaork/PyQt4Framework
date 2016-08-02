# -*- coding: utf-8 -*-

import sys
from ..protocol.stransfer import SerialTransfer

if __name__ == "__main__":
    serial_transfer = SerialTransfer(timeout=3, verbose=True)
    print serial_transfer.init("COM10", 38400, 0.02)

    # Read test
    result, data = serial_transfer.read()
    if not result:
        print "Read error:{0:s}".format(data)
        sys.exit(-1)

    global_data, package_data = data[0], data[1]
    print "Read success: global data size: {0:d}, package data size: {1:d}".\
        format(len(global_data), len(package_data))

    # Write test
    result, error = serial_transfer.write(global_data, package_data)
    if not result:
        print "Write error:{0:s}".format(error)
        sys.exit(-1)

    print "Write success!"