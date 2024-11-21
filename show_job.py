import os
import pickle

jobID = '2024_11_21_14_26_12_pmateosaparicio_2024-10-14_01_ESPM113'

# check where job is
queue_path = '/data/common/queues/step1/'
print('--------------------')
if os.path.exists(os.path.join(queue_path,jobID + '.pickle')):
    print('Job is in queue still')
    with open(os.path.join(queue_path,jobID + '.pickle'), "rb") as file: 
        queued_command = pickle.load(file)
    print('--------------------')
    print('Job contents:')
    for key, value in queued_command.items():
        print(f"{key} = {value}")

elif os.path.exists(os.path.join(queue_path,'completed',jobID+'.pickle')):
    print('Job completed')
    with open(os.path.join(queue_path,'completed',jobID + '.pickle'), "rb") as file: 
        queued_command = pickle.load(file)
    print('--------------------')
    print('Job contents:')
    for key, value in queued_command.items():
        print(f"{key} = {value}")

elif os.path.exists(os.path.join(queue_path,'failed',jobID+'.pickle')):
    print('Job failed')
    with open(os.path.join(queue_path,'failed',jobID + '.pickle'), "rb") as file: 
        queued_command = pickle.load(file)
    print('--------------------')
    print('Job contents:')
    for key, value in queued_command.items():
        print(f"{key} = {value}")

if os.path.exists(os.path.join(queue_path,'logs',jobID+'.txt')):
    # print log
    # Open the file
    print('--------------------')
    with open(os.path.join(queue_path,'logs',jobID+'.txt'), 'r') as file:
        # Read the file content
        content = file.read()

    # Print the file content
    print(content)

print('--------------------')