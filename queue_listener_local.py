# queue listener
import os
import time
import pickle
import shutil
import preprocess_step1
import preprocess_step1_meso
import time
import organise_paths
# import grp
import stat
from datetime import datetime
# import tensorflow as tf
import numpy as np
from datetime import datetime
from paramiko import SSHClient, Ed25519Key
import paramiko
from scp import SCPClient
import file_sync

q_poll_interval = 5 # in minutes

class JobScheduler:
    def __init__(self):
        self.last_30_jobs = []  # Rolling list of last 30 jobs, (runtime, user)
        self.user_runtime = {}  # User cumulative runtime in the last 30 jobs

    def is_priority_job(self, filename):
        # Check if the job filename ends with "_x.pickle"
        return filename.endswith("_x.pickle")

    def parse_filename(self, filename):
        # Extract submission date/time and user from filename
        parts = filename.split("_")
        timestamp = "_".join(parts[:6])
        submission_date = datetime.strptime(timestamp, "%Y_%m_%d_%H_%M_%S")
        user = parts[6]
        return submission_date, user

    def add_runtime(self, runtime, user):
        # Add job runtime to rolling log
        self.last_30_jobs.append((runtime, user))
        if len(self.last_30_jobs) > 30:
            old_runtime, old_user = self.last_30_jobs.pop(0)
            self.user_runtime[old_user] -= old_runtime

        # Update user runtime
        if user not in self.user_runtime:
            self.user_runtime[user] = 0
        self.user_runtime[user] += runtime
        self.user_runtime[user] = round(self.user_runtime[user])

    def sort_jobs_by_priority(self, job_files):
        # Separate priority and regular jobs
        priority_jobs = []
        regular_jobs = []

        for job in job_files:
            if self.is_priority_job(job):
                priority_jobs.append(job)
            else:
                regular_jobs.append(job)

        # Sort priority jobs by submission date
        priority_jobs.sort(key=lambda job: self.parse_filename(job)[0])

        # Group regular jobs by user
        user_jobs = {}
        job_submission_times = {}  # Store submission time for regular jobs
        for job in regular_jobs:
            submission_date, user = self.parse_filename(job)
            if user not in user_jobs:
                user_jobs[user] = []
            user_jobs[user].append(job)
            job_submission_times[job] = submission_date

        # Sort users by compute time, breaking ties by submission time of their earliest job
        sorted_users = sorted(
            user_jobs.keys(),
            key=lambda user: (
                self.user_runtime.get(user, 0),  # Primary: Least compute time
                min(job_submission_times[job] for job in user_jobs[user]) if user_jobs[user] else float('inf')  # Secondary: Earliest submission time if applicable
            )
        )

        # Write all users with runtime info to a file
        output_directory = organise_paths.queue_path()
        os.makedirs(output_directory, exist_ok=True)  # Ensure the directory exists
        output_file = os.path.join(output_directory, "user_totals.txt")
        with open(output_file, "w") as f:
            for user, runtime in sorted(self.user_runtime.items(), key=lambda x: x[1]):  # Sort all users by runtime
                f.write(f"{user} {runtime}\n")
            # print(f"User priority list written to {output_file}")

        # Sort jobs within each user's group by submission time
        for user in user_jobs:
            user_jobs[user].sort(key=lambda job: job_submission_times[job])

        # Build the sorted list of regular jobs
        sorted_regular_jobs = []
        for user in sorted_users:
            sorted_regular_jobs.extend(user_jobs[user])

        # Combine priority jobs and sorted regular jobs
        return priority_jobs + sorted_regular_jobs


scheduler = JobScheduler()

queue_path = organise_paths.queue_path()
print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Waiting for jobs...')

remote_queue_path = organise_paths.remote_queue_path()
s2p_config_root_local, s2p_config_root_remote = organise_paths.s2p_config_root()

try:
    while True:
        # update job list from server
        file_sync.sync_updated_files_from_remote(remote_dir=remote_queue_path, local_dir=queue_path)
        # update suite2p configs
        file_sync.sync_updated_files_from_remote(remote_dir=s2p_config_root_remote, local_dir=s2p_config_root_local)
        # Get list of all files in the directory
        files = os.listdir(queue_path)
        files = [file for file in files if file.endswith('.pickle')]
        prioritised_jobs = scheduler.sort_jobs_by_priority(files)

        # Write the sorted jobs to a file
        output_file = os.path.join(queue_path,'prioritised_jobs.txt')
        with open(output_file, "w") as f:
            for job in prioritised_jobs:
                f.write(f"{job}\n")    

        # if there are items in the queue
        if len(prioritised_jobs) > 0:
            try:
                files_ready = True

                # Open the job (without integrity check)
                with open(os.path.join(queue_path,prioritised_jobs[0]), "rb") as file: 
                    queued_command = pickle.load(file)

                # Cycle through the jobs trying to find one that has its files in order
                for ijob in range(len(prioritised_jobs)):
                    # assume files ready unless find otherwise
                    files_ready = True
                    
                    # Open the job
                    with open(os.path.join(queue_path,prioritised_jobs[ijob]), "rb") as file: 
                        queued_command = pickle.load(file)

                    # Integrity checks all removed for local processesing
                    # # if the experiment was done before integrity check was implemented then don't do check
                    # target_date_str = '2023-05-10' # define cutoff
                    # date_format = "%Y-%m-%d"
                    if type(queued_command['expID']) == str:
                        # make copy which is a list of 1 item
                        allExps = list([queued_command['expID']])
                    else:
                        # then it is a sequence of experiments
                        allExps = queued_command['expID']

                    # # cycle through all experiments checking integrity - only run if all files of all experiments are there
                    # for nextExpID in allExps:
                    #     animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = organise_paths.find_paths(queued_command['userID'], nextExpID)
                    #     date_str = nextExpID[:10] # get experiment date

                    #     file_date = datetime.strptime(date_str, date_format)
                    #     target_date = datetime.strptime(target_date_str, date_format)

                    #     exp_has_integrity_check = file_date >= target_date

                    #     if exp_has_integrity_check:
                    #         # you always need to have your nas data verified (contains experiment log, timeline, bonvision etc)
                    #         ready,comment = file_check_verify.verify_file_data('nas',exp_dir_raw,exp_dir_processed)
                    #         matrix_msg.main(queued_command['userID'],'----------')
                        
                    #         if not ready:
                    #             files_ready = False
                    #             matrix_msg.main(queued_command['userID'],'Awaiting NAS data integrity verification: ' + comment)
                    #         else:          
                    #             matrix_msg.main(queued_command['userID'],'NAS data verified')
                    #             print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} NAS data verified')

                    #         if queued_command['config']['runs2p']:
                    #             # if you want to do suite2p you need to have your scanimage data verified
                    #             ready,comment = file_check_verify.verify_file_data('scanimage',exp_dir_raw,exp_dir_processed)
                    #             if not ready:
                    #                 files_ready = False
                    #                 matrix_msg.main(queued_command['userID'],'Awaiting SI data integrity verification: ' + comment) 
                    #             else:          
                    #                 matrix_msg.main(queued_command['userID'],'SI data verified')
                    #                 print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} SI data verified')

                    #         if queued_command['config']['rundlc']:
                    #             # if you want to do dlc you need to have your video data verified
                    #             ready,comment = file_check_verify.verify_file_data('cams',exp_dir_raw,exp_dir_processed)
                    #             if not ready:
                    #                 files_ready = False
                    #                 matrix_msg.main(queued_command['userID'],'Awaiting video data integrity verification: ' + comment)          
                    #             else:          
                    #                 matrix_msg.main(queued_command['userID'],'video data verified')
                    #                 print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Vid data verified')
                    #     else:
                    #         # pre integrity check so just assume all files are there and run it
                    #         print('Experiment is pre 2023-05-10 so no file integrity data so assuming all data present and running')
                    #         files_ready = True

                    # if files_ready:
                    #     # then run that job
                    #     break
                files_ready = True
                # Open the job (without integrity check)

                if files_ready:
                    if type(queued_command['expID']) == str:
                        # then a single experiment
                        # expID only used here for matrix msg
                        expID = queued_command['expID']
                    else:
                        # then several experiments being run through suite2p as one
                        expID = queued_command['expID'][0]
                    
                    # if the above loop through the jobs found one that is ready
                    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Running:')
                    print(queued_command['command'])
                    
                    # ngpus = len(tf.config.list_physical_devices('GPU'))

                    # try:
                    #     assert ngpus > 0
                    # except:
                    #     print(f'GPU problems: expecting at least 1 GPU, found {ngpus}')

                    # make the output directory if it doesn't already exist (will be first expID if several are being run through suite2p together)
                    animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = organise_paths.find_paths(queued_command['userID'], allExps[0])
                    os.makedirs(exp_dir_processed, exist_ok = True) 
                    # save the command file to the output folder so that the settings field can be accessed in the pipeline
                    with open(os.path.join(exp_dir_processed,'pipeline_config.pickle'), 'wb') as f: pickle.dump(queued_command, f) 

                    start_time = time.time()
                    # run command file
                    eval(queued_command['command'])
                    # if it gets here it has somewhat worked
                    # move job to completed
                    shutil.move(os.path.join(queue_path,prioritised_jobs[ijob]),os.path.join(queue_path,'completed',prioritised_jobs[ijob]))
                    print('#####################')
                    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Completed ' + prioritised_jobs[ijob] + ' without errors')
                    print('Run time: ' + str(round((time.time()-start_time) / 60,2)) + ' mins')
                    print('#####################')
                    # delete the job file from remote queue
                    file_sync.delete_remote_file(os.path.join(remote_queue_path,prioritised_jobs[ijob]))
                    # copy data to server
                    file_sync.sync_updated_files_to_remote(local_dir=exp_dir_processed, remote_dir=organise_paths.remote_processed_data_root())
                    scheduler.add_runtime(round((time.time()-start_time) / 60,2), queued_command['userID'])  
                else:
                    # no files have been found to be ready in the queue but there are jobs in the 
                    # queue so we are probably waiting for experiments to sync to the google drive
                    # we therefore timeout for 10 mins to avoid repeatedly polling the google drive
                    # for file presence/integrity
                    print('Pausing 10 mins to await probable NAS -> GDrive sync')
                    time.sleep(60*2)
                print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Pausing before checking for new jobs')
                time.sleep(q_poll_interval*60)
            except Exception as e:              
                    
                try:
                    # some kind of error
                    queued_command['error'] = str(e)
                    # save in pickle
                    with open(os.path.join(queue_path,prioritised_jobs[ijob]), 'wb') as f: pickle.dump(queued_command, f)  
                    shutil.move(os.path.join(queue_path,prioritised_jobs[ijob]),os.path.join(queue_path,'failed',prioritised_jobs[ijob]))
                except:
                    # unable to write to command file
                    try:
                        shutil.move(os.path.join(queue_path,prioritised_jobs[ijob]),os.path.join(queue_path,'failed',prioritised_jobs[ijob]))
                    except:
                        # unable to move command file
                        # this kills the queue
                        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Error with ' + prioritised_jobs[ijob])
                        print('Unmovable file in the queue - please investigate')
                        print('Run time: ' + str((time.time()-start_time) / 60) + ' mins')
                        exit()
                    
                print('#####################')
                print('Error with ' + prioritised_jobs[ijob])
                print('Run time: ' + str((time.time()-start_time) / 60) + ' mins')
                print('#####################')            
                
            print('Waiting for jobs...')

except Exception as e:
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Error caused queue to crash!')
    print('Will require queue restart!')
    print(e)