import preprocess_step2

expIDs = ['2023-03-01_01_ESMT107']
userID = 'adamranson'

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