import preprocess_step2
import organise_paths
import grp
import os
import pickle

def run_step2_batch(step2_config):
    userID = step2_config['userID']
    expIDs = step2_config['expIDs']

    # options
    pre_secs = step2_config['pre_secs']
    post_secs = step2_config['post_secs']
    run_bonvision = step2_config['run_bonvision']
    run_s2p_timestamp = step2_config['run_s2p_timestamp']
    run_ephys = step2_config['run_ephys']
    run_dlc_timestamp = step2_config['run_dlc_timestamp']
    run_cuttraces = step2_config['run_cuttraces']

    for expID in expIDs:
        print('Starting expID...' + expID)
        # save step2 ops to exp dir
        animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = organise_paths.find_paths(userID, expID)
        with open(os.path.join(exp_dir_processed,'step2_config.pickle'), 'wb') as f: pickle.dump(step2_config, f)  
        # final ops are presecs, post secs and whether to process: 1.bonvision, 2.s2p_timestamp, 3.ephys, 4.dlc_timestamp, 5.cutraces
        preprocess_step2.run_preprocess_step2(userID,expID, pre_secs, post_secs, run_bonvision, run_s2p_timestamp, run_ephys, run_dlc_timestamp, run_cuttraces)
        
        # set permissions all files generated to user; improve this later
        animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = organise_paths.find_paths(userID, expID)
        path = exp_dir_processed
        group_id = grp.getgrnam('users').gr_gid
        mode = 0o770
        # set root exp dir
        try:
            os.chown(path, -1, group_id)
            os.chmod(path, mode)
        except:
            x=0

        for root, dirs, files in os.walk(path):
            for d in dirs:
                try:
                    dir_path = os.path.join(root, d)
                    os.chown(dir_path, -1, group_id)
                    os.chmod(dir_path, mode)
                except:
                    x=0
            for f in files:
                try:
                    file_path = os.path.join(root, f)
                    os.chown(file_path, -1, group_id)
                    os.chmod(file_path, mode)
                except:
                    x=0
