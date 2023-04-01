from datetime import datetime
import os
import pickle
import matrix_msg

expIDs = ['2023-02-24_09_ESMT116']
userID = 'adamranson'
suite2p_config = 'ch_1_depth_1.npy'
runs2p      = True 
rundlc      = False
runfitpupil = False

for expID in expIDs:

    print('Adding expID:' + expID  + ' to the queue')

    #preprocess_step1.run_preprocess_step1(userID,expID,suite2p_config,False,False,True) 
    now = datetime.now()
    command_filename = now.strftime("%Y_%m_%d_%H_%M_%S") + '_' + userID + '_' + expID + '.pickle'

    # add to queue by making a file with t
    queued_command = {}
    queued_command['command'] = 'preprocess_step1.run_preprocess_step1("' + command_filename + '","' + userID + '","' + expID + '","' \
        + suite2p_config + '",' + str(runs2p)+ ',' + str(rundlc)+ ',' + str(runfitpupil) +')'
    
    queued_command['userID'] = userID
    queued_command['expID'] = expID

    queue_path = '/data/common/queues/step1'

    # save in pickle
    with open(os.path.join(queue_path,command_filename), 'wb') as f: pickle.dump(queued_command, f)  

    files = os.listdir(queue_path)
    files = [file for file in files if os.path.isfile(os.path.join(queue_path, file))]

    matrix_msg.main(queued_command['userID'],'Added ' + queued_command['expID'] + ' to queue in position ' + str(len(files)))