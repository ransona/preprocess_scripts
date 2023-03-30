import pickle
import os

job = '2023_03_24_19_54_43_melinatimplalexi_2023-02-24_01_ESMT116.pickle'
queue_path = '/data/common/queues/step1/failed'
try:
    queued_command = pickle.load(open(os.path.join(queue_path,job), "rb"))
except:
    print('Error loading job file')

print('')
