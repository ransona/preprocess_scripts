import file_sync

def test_sync():
    local_dir = r'C:\Pipeline\Repository_Processed\complete\2025_04_29_14_12_16_adamranson_2025-04-13_03_ESYB007'
    remote_dir = '/home/adamranson/local_pipelines/AdamDellXPS15/processed_data/2025_04_29_14_12_16_adamranson_2025-04-13_03_ESYB007'

    try:
        file_sync.sync_updated_files_to_remote(local_dir, remote_dir)
        print("Sync completed successfully.")
    except Exception as e:
        print(f"Sync failed: {e}")

if __name__ == '__main__':
    test_sync()