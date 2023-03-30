from datetime import datetime
import os
import pickle

expIDs = ['2022-02-08_03_ESPM040']
userID = 'pmateosaparicio'
suite2p_config = 'ch_1_depth_1.npy'

for expID in expIDs:

    print('Adding expID:' + expID  + ' to the queue')
    runs2p      = False 
    rundlc      = False
    runfitpupil = True
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