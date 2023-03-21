import glob
import os.path
import pydub
from pydub.utils import which
import pandas as pd
import json

def find_path():
    # folder_path = r'/home/ubuntu/new/upload/*'
    folder_path = r'/home/ubuntu/production/upload/*'
    sub_folders = glob.glob(folder_path)
    the_lastest_subfolder = max(sub_folders, key=os.path.getctime)
    files = glob.glob(the_lastest_subfolder + '\*')
    the_last_file = max(files, key=os.path.getctime)
    print(the_last_file)
    return the_last_file

def find_path_folder():
    # folder_path = r'/home/ubuntu/new/upload/*'
    folder_path = r'/home/ubuntu/production/upload/*'
    sub_folders = glob.glob(folder_path)
    the_lastest_subfolder = max(sub_folders, key=os.path.getctime)
    print(the_lastest_subfolder)
    return the_lastest_subfolder
