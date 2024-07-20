'''
Script to test whether a serial connection with the force gauge can be established.
'''
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from devices import GaugeConnection
from helpers.constants import GAUGE_PORT,GAUGE_BAUD

fgu = GaugeConnection(GAUGE_PORT,GAUGE_BAUD)

def test_exists():
    assert fgu is not None

def test_connected():
    try:
        fgu.send("test")
        fgu.receive()
        sent_successfully = True
    except:
        sent_successfully = False
    assert sent_successfully == True

def test_return_error():
    fgu.send("test")
    returned = fgu.receive()
    assert returned == fgu.ERROR_CODE

def test_return_reading():
    returned = fgu.request_reading()
    assert returned != fgu.ERROR_CODE

def test_return_float():
    returned = fgu.get_force_measurement()
    assert isinstance(returned,float) == True

def test_closed():
    fgu.close()
    try:
        sent_successfully = fgu.send("test")
    except:
        sent_successfully = False
    assert sent_successfully == False

if __name__ == "__main__":
    inf_read = False
    test_exists()
    test_connected()
    test_return_error()
    test_return_reading()
    test_return_float()
    if not inf_read:
        test_closed()
    print("SUCCESS: gauge_connection testing passed")

    # infinite read loop
    if inf_read:
        try:
            while True:
                print(fgu.get_force_measurement())
        finally:
            test_closed()