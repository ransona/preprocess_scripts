from datetime import datetime
import os
import pickle
import matrix_msg
import getpass

def run_step1_batch(step1_config):

    userID = step1_config['userID']
    expIDs = step1_config['expIDs']
    suite2p_config = step1_config['suite2p_config']
    runs2p      = step1_config['runs2p']
    rundlc      = step1_config['rundlc']
    runfitpupil = step1_config['runfitpupil']

    jump_queue = step1_config['jump_queue']

    # error checking
    # check if the user who is adding the job has the same username as the directory where the job will be writing to.
    # if not stop (to avoid people overwriting each other data accidently!)
    username = getpass.getuser()
    if username != userID:
        raise ValueError("You are not permitted to execute a job on the pipeline which will write to another users data folder")

    config_path = os.path.join('/data/common/configs/s2p_configs',userID,suite2p_config)
    if not os.path.exists(config_path):
        raise FileNotFoundError('The suite2p config file does not exist: ' + config_path)

    for expID in expIDs:
        if type(expID) is str:
            # then we are not combining experiments in suite2p
            print('Adding expID:' + expID  + ' to the queue')

            #preprocess_step1.run_preprocess_step1(userID,expID,suite2p_config,False,False,True) 
            now = datetime.now()

            if jump_queue:
                command_filename = now.strftime("00_00_00_00_00_00") + '_' + userID + '_' + expID + '.pickle'
            else:
                command_filename = now.strftime("%Y_%m_%d_%H_%M_%S") + '_' + userID + '_' + expID + '.pickle'
            # add to queue by making a file with t
            queued_command = {}
            queued_command['command'] = 'preprocess_step1.run_preprocess_step1("' + command_filename + '","' + userID + '","' + expID + '","' \
                + suite2p_config + '",' + str(runs2p)+ ',' + str(rundlc)+ ',' + str(runfitpupil) +')'
            
            queued_command['userID'] = userID
            queued_command['expID'] = expID
            queued_command['config'] = {}
            queued_command['config']['runs2p'] = runs2p
            queued_command['config']['rundlc'] = rundlc
            queued_command['config']['runfitpupil'] = runfitpupil
            queued_command['config']['suite2p_config'] = suite2p_config

            queue_path = '/data/common/queues/step1'

            # save in pickle
            with open(os.path.join(queue_path,command_filename), 'wb') as f: pickle.dump(queued_command, f)  

            files = os.listdir(queue_path)
            files = [file for file in files if os.path.isfile(os.path.join(queue_path, file))]
            try:
                matrix_msg.main(queued_command['userID'],'Added ' + queued_command['expID'] + ' to queue in position ' + str(len(files)))
                matrix_msg.main('adamranson','Added ' + queued_command['expID'] + ' to queue in position ' + str(len(files)),'Server queue notifications')
            except:
                print('Error sending matrix message')

        else:
            # then we are  combining experiments in suite2p
            # iterate through experiments in list, running suite2p on all experiments together, but not the individual ones, but running the other parts 
            # of the pipeline on the individual ones
            # make the combined suite2p run - combine all expIDs into a comma seperated string            
            # then we are not combining experiments in suite2p
            print('You are combining experiments into a single suite2p run - if this is not intentional check your expID list')
            print('Adding expID:' + expID[0]  + ' to the queue as the base experiment of a ''combined experiment'' suite2p run')
            allExpIds = ','.join(expID)
            expIDsub = expID[0] # use the experiment ID of the first session

            #preprocess_step1.run_preprocess_step1(userID,expID,suite2p_config,False,False,True) 
            now = datetime.now()

            if jump_queue:
                command_filename = now.strftime("00_00_00_00_00_00") + '_' + userID + '_' + expID + '.pickle'
            else:
                command_filename = now.strftime("%Y_%m_%d_%H_%M_%S") + '_' + userID + '_' + expID[0] + '.pickle'

            # add to queue by making a file with t
            queued_command = {}
            # run pipeline on all expIDs together but without DLC or fit pupil (i.e. just suite2p)
            queued_command['command'] = 'preprocess_step1.run_preprocess_step1("' + command_filename + '","' + userID + '","' + allExpIds + '","' \
                + suite2p_config + '",' + str(runs2p)+ ',' + 'False' + ',' + 'False' +')'
            
            queued_command['userID'] = userID
            queued_command['expID'] = expID
            queued_command['config'] = {}
            queued_command['config']['runs2p'] = runs2p
            queued_command['config']['rundlc'] = False
            queued_command['config']['runfitpupil'] = False
            queued_command['config']['suite2p_config'] = suite2p_config

            queue_path = '/data/common/queues/step1'

            # save in pickle
            with open(os.path.join(queue_path,command_filename), 'wb') as f: pickle.dump(queued_command, f)  

            files = os.listdir(queue_path)
            files = [file for file in files if os.path.isfile(os.path.join(queue_path, file))]
            try:
                matrix_msg.main(queued_command['userID'],'Added ' + queued_command['expID'][0] + ' to queue in position ' + str(len(files)))
                matrix_msg.main('adamranson','Added ' + queued_command['expID'][0] + ' to queue in position ' + str(len(files)),'Server queue notifications')
            except:
                print('Error sending matrix message')
            
            for iExpID in range(len(expID)):
                expIDsub = expID[iExpID]
                print('Adding expID:' + expIDsub  + ' to the queue for non-combined processing of non-suite2p experiment data')

                #preprocess_step1.run_preprocess_step1(userID,expID,suite2p_config,False,False,True) 
                now = datetime.now()

                if jump_queue:
                    command_filename = now.strftime("00_00_00_00_00_00") + '_' + userID + '_' + expIDsub + '.pickle'
                else:
                    command_filename = now.strftime("%Y_%m_%d_%H_%M_%S") + '_' + userID + '_' + expIDsub + '.pickle'
                # add to queue by making a file with t
                queued_command = {}
                # run pipeline for each experiment seperately but not running suite2p
                queued_command['command'] = 'preprocess_step1.run_preprocess_step1("' + command_filename + '","' + userID + '","' + expIDsub + '","' \
                    + suite2p_config + '",' + 'False'+ ',' + str(rundlc)+ ',' + str(runfitpupil) +')'
                
                queued_command['userID'] = userID
                queued_command['expID'] = expIDsub
                queued_command['config'] = {}
                queued_command['config']['runs2p'] = False
                queued_command['config']['rundlc'] = rundlc
                queued_command['config']['runfitpupil'] = runfitpupil
                queued_command['config']['suite2p_config'] = suite2p_config

                queue_path = '/data/common/queues/step1'

                # save in pickle
                with open(os.path.join(queue_path,command_filename), 'wb') as f: pickle.dump(queued_command, f)  

                files = os.listdir(queue_path)
                files = [file for file in files if file.endswith('.pickle')]
                try:
                    matrix_msg.main(queued_command['userID'],'Added ' + queued_command['expID'] + ' to queue in position ' + str(len(files)))
                    matrix_msg.main('adamranson','Added ' + queued_command['expID'] + ' to queue in position ' + str(len(files)),'Server queue notifications')
                except:
                    print('Error sending matrix message')   