import preprocess_step2

expIDs = ['2023-03-01_01_ESMT107']
userID = 'adamranson'
suite2p_config = 'ch_1_depth_1.npy'

for expID in expIDs:
    print('Starting expID...' + expID)
    # final ops are presecs, post secs and whether to process: 1.bonvision, 2.s2p_timestamp, 3.ephys, 4.dlc_timestamp, 5.cutraces
    preprocess_step2.run_preprocess_step2(userID,expID, 5, 5, False,True,False,False,False)