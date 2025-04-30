import file_sync

# Upload changed files from local to remote
file_sync.sync_updated_files_to_remote(
    host='158.109.215.222',
    port=10022,
    username='adamranson',
    key_path='C:/Users/ranso/.ssh/id_ed25519',
    local_dir='C:/Pipeline/queues/step1',
    remote_dir='/home/adamranson/local_pipelines/AdamDellXPS15/queues/step1'
)

# Download changed files from remote to local
file_sync.sync_updated_files_from_remote(
    host='158.109.215.222',
    port=10022,
    username='adamranson',
    key_path='C:/Users/ranso/.ssh/id_ed25519',
    remote_dir='/home/adamranson/local_pipelines/AdamDellXPS15/queues/step1',
    local_dir='C:/Pipeline/queues/step1'
)
