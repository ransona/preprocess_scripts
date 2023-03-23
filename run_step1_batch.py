import preprocess_step1

expIDs = ['2023-03-01_01_ESMT107']
userID = 'adamranson'
suite2p_config = 'ch_1_depth_1.npy'

for expID in expIDs:
    print('Starting expID...')
    # the last "True, True" determined if you run suite2p and dlc respectively
    preprocess_step1.run_preprocess_step1(userID,expID,suite2p_config,False,False,True) 