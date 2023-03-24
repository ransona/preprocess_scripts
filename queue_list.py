# queue listener
import os
import time
import pickle
import shutil
import preprocess_step1

queue_path = '/data/common/queues/step1'

files = os.listdir(queue_path)
files = [file for file in files if os.path.isfile(os.path.join(queue_path, file))]
if len(files) > 0:
    # Sort the files by name
    files_sorted = sorted(files)
    print('Queued jobs:')
    print(files_sorted)