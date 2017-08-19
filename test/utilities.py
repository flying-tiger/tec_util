import os
import sys
from os.path import dirname, abspath, join

test_root = dirname(abspath(__file__))

def data_item_path(name):
    ''' Get abspath to a test data item '''
    return join(test_root, 'data', name)

def open_datafile(name):
    ''' Get read-only handle to test data file '''
    return open(data_item_path(name), 'r')
