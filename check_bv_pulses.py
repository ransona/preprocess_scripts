import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from scipy import interpolate
from scipy.io import loadmat
import matplotlib.pyplot as plt
import organise_paths
import pickle


userID = 'melinatimplalexi'
expID = '2024-09-04_03_ESMT186'

animalID, remote_repository_root, \
processed_root, exp_dir_processed, \
    exp_dir_raw = organise_paths.find_paths(userID, expID)
exp_dir_processed_recordings = os.path.join(processed_root, animalID, expID,'recordings')
# load the stimulus parameter file produced by matlab by the bGUI
# this includes stim parameters and stimulus order
try:
    stim_params = loadmat(os.path.join(exp_dir_raw, expID + '_stim.mat'))
except:
    raise Exception('Stimulus parameter file not found - this experiment was probably from pre-Dec 2021.')
# load timeline
Timeline = loadmat(os.path.join(exp_dir_raw, expID + '_Timeline.mat'))
Timeline = Timeline['timelineSession']
# get timeline file in a usable format after importing to python
tl_chNames = Timeline['chNames'][0][0][0][0:]
tl_daqData = Timeline['daqData'][0,0]
tl_time    = Timeline['time'][0][0]

frame_events = pd.read_csv(os.path.join(exp_dir_raw, expID + '_FrameEvents.csv'), names=['Frame', 'Timestamp', 'Sync', 'Trial'],
                        header=None, skiprows=[0], dtype={'Frame':np.float32, 'Timestamp':np.float32, 'Sync':np.float32, 'Trial':np.float32})

# Find BV times when digital flips
Timestamp = frame_events['Timestamp'].values
Sync = frame_events['Sync'].values
Trial = frame_events['Trial']

# if Sync[0] == 1:
#     sync_polarity = -1
# else:
#     sync_polarity = 1
sync_polarity = -1

flip_times_bv = np.squeeze(Timestamp[np.where((np.diff(Sync) == sync_polarity))[0]])

# Find TL times when digital flips
bv_ch = np.where(np.isin(tl_chNames, 'Bonvision'))
tl_dig_thresholded = np.squeeze((tl_daqData[:, bv_ch] > 2.5).astype(int))
flip_times_tl = np.squeeze(tl_time[0,np.where(np.diff(tl_dig_thresholded) == sync_polarity)])

# Find PD ch
# pd_ch = np.where(np.isin(tl_chNames, 'Photodiode'))
# plt.plot(np.squeeze(tl_daqData[:, pd_ch]))
# plt.plot(np.squeeze(tl_daqData[:, bv_ch]))
# plt.show()
# plt.figure()
# plt.plot(Timestamp,Sync,label='BV')
# plt.plot(tl_time[0],tl_dig_thresholded,label='TL')
# plt.legend()
# plt.show()


# if Sync[0] == 1:
#     # if it starts high, remove the first flip
#     flip_times_tl = flip_times_tl[1:]

# compare bv and tl flip time intervals
bv_flip_intervals = np.diff(flip_times_bv)
tl_flip_intervals = np.diff(flip_times_tl)
# plt.plot(bv_flip_intervals, label='BV')
# plt.plot(tl_flip_intervals, label='TL')
# plt.legend()
# plt.show(block=False)

# Calc corr to check TL and BV timing pulses are aligned
trace1 = bv_flip_intervals.astype(float)
trace2 = tl_flip_intervals.astype(float)
trace1 = (trace1 - np.mean(trace1)) / np.std(trace1)
trace2 = (trace2 - np.mean(trace2)) / np.std(trace2)

min_length = min(len(trace1), len(tl_flip_intervals))

trace1 = trace1[0:min_length]
trace2 = trace2[0:min_length]

correlation = np.correlate(trace1, trace2, mode='full')
lags = np.arange(-len(trace1) + 1, len(trace1))
# Find the lag corresponding to the maximum correlation
max_correlation_index = np.argmax(correlation)
lag_in_samples = lags[max_correlation_index]

if lag_in_samples != 0:
    lag_in_samples = lag_in_samples * -1
    print('Timeline and Bonvision pulses are not well aligned. Please reprocess this experiment in stage 2')
else:
    print('Timeline and Bonvision pulses are well aligned!')


# flip_times_bv_old = np.squeeze(Timestamp[np.where((np.diff(Sync) == -1))[0]])
# flip_times_bv = np.squeeze(Timestamp[np.where((np.diff(Sync) == 1))[0]])

# # Find TL times when digital flips
# bv_ch = np.where(np.isin(tl_chNames, 'Bonvision'))
# tl_dig_thresholded = np.squeeze((tl_daqData[:, bv_ch] > 2.5).astype(int))

# # Find PD ch
# pd_ch = np.where(np.isin(tl_chNames, 'Photodiode'))
# # plt.plot(np.squeeze(tl_daqData[:, pd_ch]))
# # plt.plot(np.squeeze(tl_daqData[:, bv_ch]))
# # plt.show()

# flip_times_tl_old = np.squeeze(tl_time[0,np.where(np.diff(tl_dig_thresholded) == -1)])
# flip_times_tl = np.squeeze(tl_time[0,np.where(np.diff(tl_dig_thresholded) == 1)])

# # compare bv and tl flip time intervals
# # bv_flip_intervals = np.diff(flip_times_bv)
# # tl_flip_intervals = np.diff(flip_times_tl)
# # plt.plot(bv_flip_intervals, label='BV')
# # plt.plot(tl_flip_intervals, label='TL')
# # plt.legend()
# # plt.show()


# # Check NI DAQ caught as many sync pulses as BV produced
# pulse_diff_old = len(flip_times_tl_old) - len(flip_times_bv_old)
# pulse_diff = len(flip_times_tl) - len(flip_times_bv)

# print('WITH OLD PIPELINE:')
# if pulse_diff_old > 0:
#     print(str(pulse_diff_old) + ' more pulse(s) in TL')
#     print('Error: pulse mismatch - with old processing method')
#     if pulse_diff_old > 1:
#         print('There is more than 1 extra pulse so please tell Adam expID!')
# elif pulse_diff < 0:
#     print(str(pulse_diff_old * -1) + ' more pulse(s) in BV')
#     print('Error: pulse mismatch - with old processing method,  please tell Adam expID!')
# else:
#     print('Pulse match with old processing method! No need to reprocess data')

# print('WITH NEW PIPELINE:')
# if pulse_diff > 0:
#     print(str(pulse_diff) + ' more pulse(s) in TL')
#     print('Error: pulse mismatch with new method - please tell Adam')
# elif pulse_diff < 0:
#     print(str(pulse_diff * -1) + ' more pulse(s) in BV')
#     print('Error: pulse mismatch with new method - please tell Adam')
# else:
#     print('Pulse match with new processing method!')
#     if pulse_diff_old != 0:
#         print('**REPROCESS THIS EXPERIMENT IN STAGE 2**')

