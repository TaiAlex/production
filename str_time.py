import datetime
from datetime import datetime, timezone, timedelta
import pytz
import os
from os import path


def now_utc():
    now = datetime.utcnow()
    now = now.replace(tzinfo=pytz.utc)
    return now

# def str_yyyy_mm_from_int(year, month, space = '-'):
#     if month < 10:
#         str_month = '0'+ str(month)
#     else:
#         str_month = str(month)
#     return str(year) + space + str_month

def str_yyyy_mm_dd(time: datetime = now_utc(), space = "-"):
    str_year = str(time.year)
    if time.month < 10:
        str_month = '0'+ str(time.month)
    else:
        str_month = str(time.month)
    if time.day < 10:
        str_day = '0'+ str(time.day)
    else:
        str_day = str(time.day)
    return str_day + space + str_month + space + str_year

# def str_yyyy_mm(time = now_utc(), space = "-"):
#     str_year = str(time.year)
#     if time.month < 10:
#         str_month = '0'+ str(time.month)
#     else:
#         str_month = str(time.month)
#     return  str_year + space + str_month

def create_path(path_dir):
    if path.exists(path_dir):
        pass
    else:
        os.mkdir(path_dir)
        
def upload_file_bytes(file_bytes, path):
    f = open(path, "wb")
    f.write(file_bytes)
    f.close()
    
def get_time():
    current = datetime.now()
    time = str(current.strftime("%H%M%S"))
    return time
