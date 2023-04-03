# queue listener
import os
import time
import pickle
import shutil
import preprocess_step1
import matrix_msg
import time

try:
    matrix_msg.main('adamranson','Queue restarted')
    matrix_msg.main('adamranson','Queue restarted','Server queue notifications')
except:
    print('Error sending element notification')

queue_path = '/data/common/queues/step1'
print('Waiting for jobs...')
while True:
    # Get list of all files in the directory
    time.sleep(0.5)
    files = os.listdir(queue_path)
    files = [file for file in files if os.path.isfile(os.path.join(queue_path, file))]
    if len(files) > 0:
        try:
            start_time = time.time()
            # Sort the files by name (which will put the oldest at the top of the list)
            files_sorted = sorted(files)
            # Run the next job
            with open(os.path.join(queue_path,files_sorted[0]), "rb") as file: 
                queued_command = pickle.load(file)

            print('Running:')
            print(queued_command['command'])

            try:
                matrix_msg.main(queued_command['userID'],'Starting ' + queued_command['expID'])
                matrix_msg.main('adamranson','Starting ' + queued_command['expID'],'Server queue notifications')
            except:
                print('Error sending element notification')

            eval(queued_command['command'])
            
            # if it gets here it has somewhat worked
            # move job to completed
            shutil.move(os.path.join(queue_path,files_sorted[0]),os.path.join(queue_path,'completed',files_sorted[0]))
            print('#####################')
            print('Completed ' + files_sorted[0] + ' without errors')
            print('Run time: ' + str(round((time.time()-start_time) / 60,2)) + ' mins')
            print('#####################')
            
            try:
                matrix_msg.main(queued_command['userID'],'Complete ' + files_sorted[0] + ' without errors')
                matrix_msg.main(queued_command['userID'],'Run time: ' + str(round((time.time()-start_time) / 60,2)) + ' mins')
                matrix_msg.main('adamranson','Complete ' + files_sorted[0] + ' without errors','Server queue notifications')
                matrix_msg.main('adamranson','Run time: ' + str(round((time.time()-start_time) / 60,2)) + ' mins','Server queue notifications')
            except:
                print('Error sending element notification')

            print('Waiting for jobs...')

        except Exception as e:

            try:
                matrix_msg.main(queued_command['userID'],'Error running ' + files_sorted[0])
                matrix_msg.main(queued_command['userID'],str(e))
                matrix_msg.main(queued_command['userID'],'Run time: ' + str(round((time.time()-start_time) / 60,2)) + ' mins')
                matrix_msg.main('adamranson','Error running ' + files_sorted[0],'Server queue notifications')
                matrix_msg.main('adamranson',str(e),'Server queue notifications')
                matrix_msg.main('adamranson','Run time: ' + str(round((time.time()-start_time) / 60,2)) + ' mins','Server queue notifications')                
            except:
                print('Error sending element notification')
                
            try:
                # some kind of error
                queued_command['error'] = str(e)
                # save in pickle
                with open(os.path.join(queue_path,files_sorted[0]), 'wb') as f: pickle.dump(queued_command, f)  
                shutil.move(os.path.join(queue_path,files_sorted[0]),os.path.join(queue_path,'failed',files_sorted[0]))
            except:
                # unable to write to command file
                try:
                    shutil.move(os.path.join(queue_path,files_sorted[0]),os.path.join(queue_path,'failed',files_sorted[0]))
                except:
                    # unable to move command file
                    # this kills the queue
                    print('Error with ' + files_sorted[0])
                    print('Unmovable file in the queue - please investigate')
                    print('Run time: ' + str((time.time()-start_time) / 60) + ' mins')
                    exit()
                
            print('#####################')
            print('Error with ' + files_sorted[0])
            print('Run time: ' + str((time.time()-start_time) / 60) + ' mins')
            print('#####################')
        print('Waiting for jobs...')