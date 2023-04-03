import preprocess_step2
import organise_paths
import grp
import stat
import os

expIDs = ['2023-02-24_09_ESMT116']
userID = 'melinatimplalexi'

# options
pre_secs = 5
post_secs = 5
run_bonvision = True
run_s2p_timestamp = True
run_ephys = True
run_dlc_timestamp = True
run_cuttraces = True

for expID in expIDs:
    print('Starting expID...' + expID)
    # final ops are presecs, post secs and whether to process: 1.bonvision, 2.s2p_timestamp, 3.ephys, 4.dlc_timestamp, 5.cutraces
    preprocess_step2.run_preprocess_step2(userID,expID, pre_secs, post_secs, run_bonvision, run_s2p_timestamp, run_ephys, run_dlc_timestamp, run_cuttraces)
    # set permissions all files generated to user
    try:
        animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = organise_paths.find_paths(userID, expID)
        path = exp_dir_processed
        group_id = grp.getgrnam('users').gr_gid
        mode = 0o770
        for root, dirs, files in os.walk(path):
            for d in dirs:
                dir_path = os.path.join(root, d)
                os.chown(dir_path, -1, group_id)
                os.chmod(dir_path, mode)
            for f in files:
                file_path = os.path.join(root, f)
                os.chown(file_path, -1, group_id)
                os.chmod(file_path, mode)
    except:
        print('Problem setting file permissions to user in step 1 batch')