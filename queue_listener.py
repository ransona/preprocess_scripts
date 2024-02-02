# queue listener
import os
import time
import pickle
import shutil
import preprocess_step1
import matrix_msg
import time
import organise_paths
import grp
import stat
import file_check_verify
from datetime import datetime
import tensorflow as tf

matrix_msg.main('adamranson','Queue restarted')
matrix_msg.main('adamranson','Queue restarted','Server queue notifications')

queue_path = '/data/common/queues/step1'
print('Waiting for jobs...')
while True:
    # Get list of all files in the directory
    time.sleep(0.5)
    files = os.listdir(queue_path)
    files = [file for file in files if file.endswith('.pickle')]
    # if there are items in the queue
    if len(files) > 0:
        try:
            start_time = time.time()
            # Sort the files by name (which will put the oldest at the top of the list)
            files_sorted = sorted(files)
            files_ready = True

            # Open the job (without integrity check)
            with open(os.path.join(queue_path,files_sorted[0]), "rb") as file: 
                queued_command = pickle.load(file)

            # Cycle through the jobs trying to find one that has its files in order
            for ijob in range(len(files_sorted)):
                # assume files ready unless find otherwise
                files_ready = True
                
                # Open the job
                with open(os.path.join(queue_path,files_sorted[ijob]), "rb") as file: 
                    queued_command = pickle.load(file)

                # if the experiment was done before integrity check was implemented then don't do check
                target_date_str = '2023-05-10' # define cutoff
                date_format = "%Y-%m-%d"
                if type(queued_command['expID']) == str:
                    date_str = queued_command['expID'][:10] # get experiment date
                    # pull out paths for experiment    
                    animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = organise_paths.find_paths(queued_command['userID'], queued_command['expID'])
                else:
                    # then it is a sequence of experiments
                    # integrity check needs to be implemented here
                    date_str = '2023-05-09' # spoof earlier date to skip integrity check
                    # pull out paths for experiment    
                    animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = organise_paths.find_paths(queued_command['userID'], queued_command['expID'][0])                    

                file_date = datetime.strptime(date_str, date_format)
                target_date = datetime.strptime(target_date_str, date_format)

                exp_has_integrity_check = file_date >= target_date

                if exp_has_integrity_check:
                    # you always need to have your nas data verified (contains experiment log, timeline, bonvision etc)
                    ready,comment = file_check_verify.verify_file_data('nas',exp_dir_raw,exp_dir_processed)
                    matrix_msg.main(queued_command['userID'],'----------')
                
                    if not ready:
                        files_ready = False
                        matrix_msg.main(queued_command['userID'],'Awaiting NAS data integrity verification: ' + comment)
                    else:          
                        matrix_msg.main(queued_command['userID'],'NAS data verified')
                        print('NAS data verified')

                    if queued_command['config']['runs2p']:
                        # if you want to do suite2p you need to have your scanimage data verified
                        ready,comment = file_check_verify.verify_file_data('scanimage',exp_dir_raw,exp_dir_processed)
                        if not ready:
                            files_ready = False
                            matrix_msg.main(queued_command['userID'],'Awaiting SI data integrity verification: ' + comment) 
                        else:          
                            matrix_msg.main(queued_command['userID'],'SI data verified')
                            print('SI data verified')

                    if queued_command['config']['rundlc']:
                        # if you want to do dlc you need to have your video data verified
                        ready,comment = file_check_verify.verify_file_data('cams',exp_dir_raw,exp_dir_processed)
                        if not ready:
                            files_ready = False
                            matrix_msg.main(queued_command['userID'],'Awaiting video data integrity verification: ' + comment)          
                        else:          
                            matrix_msg.main(queued_command['userID'],'video data verified')
                            print('Vid data verified')
                else:
                    # pre integrity check so just assume all files are there and run it
                    print('Experiment is pre 2023-05-10 so no file integrity data so assuming all data present and running')
                    files_ready = True

                if files_ready:
                    # then run that job
                    break

            if files_ready:
                if type(queued_command['expID']) == str:
                    # then a single experiment
                    # expID only used here for matrix msg
                    expID = queued_command['expID']
                else:
                    # then several experiments being run through suite2p as one
                    expID = queued_command['expID'][0]
                    matrix_msg.main(queued_command['userID'],'Running COMBINED experiment')

                matrix_msg.main(queued_command['userID'],'----------')
                
                # if the above loop through the jobs found one that is ready
                print('Running:')
                print(queued_command['command'])

                matrix_msg.main(queued_command['userID'],'Starting ' + expID)
                matrix_msg.main('adamranson','Starting ' + expID,'Server queue notifications')
                
                try:
                    assert len(tf.config.list_physical_devices('GPU')) == 1
                except:
                    print('GPU problems')
                    matrix_msg.main(queued_command['userID'],'GPU problem detected')
                    matrix_msg.main('adamranson','GPU problem detected')


                eval(queued_command['command'])
                
                # if it gets here it has somewhat worked
                # move job to completed
                shutil.move(os.path.join(queue_path,files_sorted[0]),os.path.join(queue_path,'completed',files_sorted[0]))
                print('#####################')
                print('Completed ' + files_sorted[0] + ' without errors')
                print('Run time: ' + str(round((time.time()-start_time) / 60,2)) + ' mins')
                print('#####################')

                matrix_msg.main(queued_command['userID'],'Complete ' + files_sorted[0] + ' without errors')
                matrix_msg.main(queued_command['userID'],'Run time: ' + str(round((time.time()-start_time) / 60,2)) + ' mins')
                matrix_msg.main('adamranson','Complete ' + files_sorted[0] + ' without errors','Server queue notifications')
                matrix_msg.main('adamranson','Run time: ' + str(round((time.time()-start_time) / 60,2)) + ' mins','Server queue notifications')
            else:
                # no files have been found to be ready in the queue but there are jobs in the 
                # queue so we are probably waiting for experiments to sync to the google drive
                # we therefore timeout for 10 mins to avoid repeatedly polling the google drive
                # for file presence/integrity
                print('Pausing 10 mins to await probable NAS -> GDrive sync')
                time.sleep(60*10)

        except Exception as e:

            matrix_msg.main(queued_command['userID'],'Error running ' + files_sorted[0])
            matrix_msg.main(queued_command['userID'],str(e))
            matrix_msg.main(queued_command['userID'],'Run time: ' + str(round((time.time()-start_time) / 60,2)) + ' mins')
            matrix_msg.main('adamranson','Error running ' + files_sorted[0],'Server queue notifications')
            matrix_msg.main('adamranson',str(e),'Server queue notifications')
            matrix_msg.main('adamranson','Run time: ' + str(round((time.time()-start_time) / 60,2)) + ' mins','Server queue notifications')                
                
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