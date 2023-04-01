import pickle
import os

job = '2023_03_31_00_21_17_melinatimplalexi_2023-02-28_15_ESMT116.pickle'
queue_path = '/data/common/queues/step1/failed'
try:
    queued_command = pickle.load(open(os.path.join(queue_path,job), "rb"))
except:
    print('Error loading job file')
    
print('Command run:')
print(queued_command['command'])
print('Error:')
print(queued_command['error'])