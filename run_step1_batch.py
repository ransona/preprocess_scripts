from datetime import datetime
import os
import pickle
import matrix_msg

def run_step1_batch(step1_config):

    userID = step1_config['userID']
    expIDs = step1_config['expIDs']
    suite2p_config = step1_config['suite2p_config']
    runs2p      = step1_config['runs2p']
    rundlc      = step1_config['rundlc']
    runfitpupil = step1_config['runfitpupil']

    jump_queue = step1_config['jump_queue']

    # error checking
    config_path = os.path.join('/data/common/configs/s2p_configs',userID,suite2p_config)
    if not os.path.exists(config_path):
        raise FileNotFoundError('The suite2p config file does not exist: ' + config_path)

    for expID in expIDs:

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
        queued_command['config']['runfitpupil'] = rundlc
        queued_command['config']['suite2p_config'] = rundlc

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