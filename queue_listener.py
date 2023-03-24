# queue listener
import os
import time
import pickle
import shutil
import preprocess_step1

queue_path = '/data/common/queues/step1'
print('Waiting for jobs...')
while True:
    # Get list of all files in the directory
    time.sleep(4)
    files = os.listdir(queue_path)
    files = [file for file in files if os.path.isfile(os.path.join(queue_path, file))]
    if len(files) > 0:
        # Sort the files by name
        files_sorted = sorted(files)
        # Run the next job
        queued_command = pickle.load(open(os.path.join(queue_path,files_sorted[0]), "rb"))
        print('Running:')
        print(queued_command)
        try:
            eval(queued_command['command'])
            # if it gets here it has somewhat worked
            # move job to completed
            shutil.move(os.path.join(queue_path,files_sorted[0]),os.path.join(queue_path,'completed',files_sorted[0]))
            print('#####################')
            print('Complete ' + files_sorted[0] + ' without errors:')
            print('#####################')
            print('Waiting for jobs...')
        except Exception as e:
            # some kind of error
            queued_command['error'] = str(e)
            shutil.move(os.path.join(queue_path,files_sorted[0]),os.path.join(queue_path,'failed',files_sorted[0]))
            print('#####################')
            print('Error with ' + files_sorted[0])
            print('#####################')
            print('Waiting for jobs...')
                  