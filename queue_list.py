# queue listener
import os
import time
import pickle
import shutil
import preprocess_step1

queue_path = '/data/common/queues/step1'

files = os.listdir(queue_path)
files = os.listdir(queue_path)
files = [file for file in files if file.endswith('.pickle')]

if len(files) > 0:
    # Sort the files by name
    files_sorted = sorted(files)
    print('Queued jobs:')
    print(files_sorted)
else:
    print('Nothing found in queue')