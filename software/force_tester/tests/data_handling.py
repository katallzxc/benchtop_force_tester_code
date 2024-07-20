'''
Script to test functions for handling (recording + analyzing) force tester data.
'''
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import main
import record
from helpers import files

DESCRIPTORS = record.DATA_TYPE_NAMES
HEADERS = record.DATA_HEADERS
DEVICE = main.TEST_DEVICE_ID
print(DEVICE)

def test_get_path():
    test_path = files.get_path()
    print(test_path)
    assert test_path!="", "path is empty"

def test_save_data():
    try:
        test_time = files.get_timestamp()
        test_data = record.make_dummy_dict(False)
        test_path = files.get_path()
        record.export_outputs(test_data,test_path,"test",test_time,files.FORCE_TYPE)
        sent_successfully = True
    except:
        sent_successfully = False
    assert sent_successfully == True

def test_save_params(test_df):
    record.export_outputs(test_df)

def test_params_main(test_dict,strdesc):
    test_dict = main.fill_parameter_dict(test_dict,strdesc,DEVICE)
    return test_dict

if __name__ == "__main__":
    print("entered test")
    test_get_path()
    test_save_data()
    print("SUCCESS: gauge_connection testing passed")
    