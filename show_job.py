import os
import pickle

jobID = '2023_06_13_16_34_32_pmateosaparicio_2023-06-12_02_ESPM096'

# check where job is
queue_path = '/data/common/queues/step1'
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