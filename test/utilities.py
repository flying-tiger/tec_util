import contextlib
import os
import sys
import tempfile

test_root = os.path.dirname(os.path.abspath(__file__))

def data_item_path(name):
    ''' Get abspath to a test data item '''
    return os.path.join(test_root, 'data', name)

def open_datafile(name):
    ''' Get read-only handle to test data file '''
    return open(data_item_path(name), 'r')

@contextlib.contextmanager
def temp_workspace():
    ''' Create and chdir into temp directory. chdir back when done '''
    home = os.getcwd()
    with tempfile.TemporaryDirectory() as temp:
        try:
            os.chdir(temp)
            yield
        finally:
            os.chdir(home)

