from datetime import datetime
import os
import pickle
import matrix_msg

# expID is a nested list whereby the items in the nested group get sent through suite2p together then get split
# how will this work with multi plane imaging when not all depths might have a frame... to be tested
expIDs = [['2023-02-28_13_ESMT116','2023-02-28_14_ESMT116']]
userID = 'adamranson'
suite2p_config = 'ch_1_depth_1.npy'
runs2p      = True 
rundlc      = True
runfitpupil = True

jump_queue = False

for expID in expIDs:
    if len(expID)==1:
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
        # make the combined suite2p run
        # combine all expIDs into a comma seperated string
        allExpIds = ','.join(expID)
        expIDsub = expID[0] # use the experiment ID of the first session
        now = datetime.now()
        command_filename = now.strftime("%Y_%m_%d_%H_%M_%S") + '_' + userID + '_' + expIDsub + '.pickle'
        queued_command = {}
        # will only run s2p:
        queued_command['command'] = 'preprocess_step1.run_preprocess_step1("' + command_filename + '","' + userID + '","' + allExpIds + '","' \
            + suite2p_config + '",' + str(runs2p)+ ',' + str(False)+ ',' + str(False) +')'
        
        queued_command['userID'] = userID
        queued_command['expID'] = expID # this a list, not just a single item
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
            matrix_msg.main(queued_command['userID'],'Added ' + queued_command['expID'] + ' to queue in position ' + str(len(files)))
            matrix_msg.main('adamranson','Added ' + queued_command['expID'] + ' to queue in position ' + str(len(files)),'Server queue notifications')
        except:
            print('Error sending matrix message')

        for iExpID in range(len(expID)):
            expIDsub = expID[iExpID]
            print('Adding expID:' + expIDsub  + ' to the queue')

            #preprocess_step1.run_preprocess_step1(userID,expID,suite2p_config,False,False,True) 
            now = datetime.now()

            if jump_queue:
                command_filename = now.strftime("00_00_00_00_00_00") + '_' + userID + '_' + expIDsub + '.pickle'
            else:
                command_filename = now.strftime("%Y_%m_%d_%H_%M_%S") + '_' + userID + '_' + expIDsub + '.pickle'

            queued_command = {}
            queued_command['command'] = 'preprocess_step1.run_preprocess_step1("' + command_filename + '","' + userID + '","' + expIDsub + '","' \
                + suite2p_config + '",' + str(runs2p)+ ',' + str(rundlc)+ ',' + str(runfitpupil) +')'
            
            queued_command['userID'] = userID
            queued_command['expID'] = expIDsub
            queued_command['config'] = {}

            queued_command['config']['runs2p'] = False # because suite2p is run above as combination of experiments
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