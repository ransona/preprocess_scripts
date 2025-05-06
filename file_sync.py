import os
import time
from paramiko import SSHClient, Ed25519Key, AutoAddPolicy
import stat
import organise_paths  # assumes this module exists and provides get_ssh_settings()
from datetime import datetime
import sys
import subprocess
from pathlib import Path

# WSL SSH key setup needed to make private key suitably secure:
# mkdir -p ~/.ssh
# cp /mnt/c/Users/ranso/.ssh/id_ed25519 ~/.ssh/
# chmod 600 ~/.ssh/id_ed25519

def list_local_files(base_path):
    files = {}
    for root, _, filenames in os.walk(base_path):
        for name in filenames:
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, base_path).replace("\\", "/")
            stat_info = os.stat(full_path)
            files[rel_path] = (stat_info.st_mtime, stat_info.st_size)
    return files

def list_remote_files(sftp, base_path):
    files = {}
    def walk(path):
        try:
            for item in sftp.listdir_attr(path):
                remote_path = f"{path}/{item.filename}"
                if stat.S_ISDIR(item.st_mode):
                    walk(remote_path)
                else:
                    rel_path = os.path.relpath(remote_path, base_path).replace("\\", "/")
                    files[rel_path] = (item.st_mtime, item.st_size)
        except FileNotFoundError:
            pass
    walk(base_path)
    return files

def list_local_dirs(base_path):
    dirs = []
    for root, dirs_in_root, _ in os.walk(base_path):
        for d in dirs_in_root:
            full_path = os.path.join(root, d)
            rel_path = os.path.relpath(full_path, base_path).replace("\\", "/")
            dirs.append(rel_path)
    return dirs

def list_remote_dirs(sftp, base_path):
    dirs = []
    def walk(path):
        try:
            for item in sftp.listdir_attr(path):
                remote_path = f"{path}/{item.filename}"
                if stat.S_ISDIR(item.st_mode):
                    rel_path = os.path.relpath(remote_path, base_path).replace("\\", "/")
                    dirs.append(rel_path)
                    walk(remote_path)
        except FileNotFoundError:
            pass
    walk(base_path)
    return dirs

def ensure_remote_dir(sftp, remote_path):
    parts = remote_path.strip("/").split("/")
    path = ""
    for part in parts:
        path += "/" + part
        try:
            sftp.stat(path)
        except FileNotFoundError:
            sftp.mkdir(path)

def ensure_local_dir(local_path):
    os.makedirs(local_path, exist_ok=True)


def sync_updated_files_to_remote(local_dir, remote_dir):
    host, port, username, key_path = organise_paths.get_ssh_settings()

    # Convert Windows local path to WSL-style
    local_dir = Path(local_dir).resolve()
    local_path_wsl = str(local_dir).replace(":", "").replace("\\", "/")
    local_path_wsl = f"/mnt/{local_path_wsl[0].lower()}{local_path_wsl[1:]}/"  

    # Compose the rsync command
    rsync_cmd = (
        f'wsl rsync -az --progress -e "ssh -i {key_path} -p {port}" '
        f'"{local_path_wsl}" {username}@{host}:"{remote_dir}"'
    )

    print(f"Running: {rsync_cmd}\n")

    # Run the command with live output
    subprocess.run(rsync_cmd, shell=True, check=True)

# def sync_updated_files_to_remote(local_dir, remote_dir):
#     host, port, username, key_path = organise_paths.get_ssh_settings()
#     key = Ed25519Key.from_private_key_file(key_path)
#     ssh = SSHClient()
#     ssh.set_missing_host_key_policy(AutoAddPolicy())
#     ssh.connect(hostname=host, port=port, username=username, pkey=key)
#     sftp = ssh.open_sftp()

#     local_dirs = list_local_dirs(local_dir)
#     remote_dirs = set(list_remote_dirs(sftp, remote_dir))

#     for rel_dir in local_dirs:
#         if rel_dir not in remote_dirs:
#             remote_path = f"{remote_dir}/{rel_dir}".replace("\\", "/")
#             ensure_remote_dir(sftp, remote_path)
#             print(f"Creating remote folder: {rel_dir}")

#     local_files = list_local_files(local_dir)
#     remote_files = list_remote_files(sftp, remote_dir)

#     for rel_path, (local_mtime, local_size) in local_files.items():
#         remote_info = remote_files.get(rel_path)
#         should_upload = (
#             remote_info is None or
#             local_mtime > remote_info[0] or
#             local_size != remote_info[1]
#         )
#         if should_upload:
#             local_path = os.path.join(local_dir, rel_path)
#             remote_path = f"{remote_dir}/{rel_path}".replace("\\", "/")
#             ensure_remote_dir(sftp, os.path.dirname(remote_path))
#             t0 = time.time()
#             sys.stdout.write(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Uploading {rel_path}...') 
#             sys.stdout.flush()                 
#             # sftp.put(local_path, remote_path)
#             with open(local_path, 'rb') as local_file:
#                 with sftp.file(remote_path, 'wb') as remote_file:
#                     while True:
#                         data = local_file.read(32675)  # 1MB buffer
#                         if not data:
#                             break
#                         remote_file.write(data)
#             transfer_speed = round((os.path.getsize(local_path) / (1024 * 1024)) / (time.time() - t0), 2)            
#             sys.stdout.write(f' done in {(time.time() - t0)/60:.2f} mins ({transfer_speed}MB/s)\n')            

#     sftp.close()
#     ssh.close()



# def sync_updated_files_from_remote(remote_dir, local_dir):
#     host, port, username, key_path = organise_paths.get_ssh_settings()
#     key = Ed25519Key.from_private_key_file(key_path)
#     ssh = SSHClient()
#     ssh.set_missing_host_key_policy(AutoAddPolicy())
#     ssh.connect(hostname=host, port=port, username=username, pkey=key)
#     sftp = ssh.open_sftp()

#     local_dirs = set(list_local_dirs(local_dir))
#     remote_dirs = list_remote_dirs(sftp, remote_dir)

#     for rel_dir in remote_dirs:
#         if rel_dir not in local_dirs:
#             local_path = os.path.join(local_dir, rel_dir)
#             ensure_local_dir(local_path)
#             print(f"Creating local folder: {rel_dir}")

#     local_files = list_local_files(local_dir)
#     remote_files = list_remote_files(sftp, remote_dir)

#     for rel_path, (remote_mtime, remote_size) in remote_files.items():
#         local_info = local_files.get(rel_path)
#         should_download = (
#             local_info is None or
#             remote_mtime > local_info[0] or
#             remote_size != local_info[1]
#         )
#         if should_download:
#             remote_path = f"{remote_dir}/{rel_path}".replace("\\", "/")
#             local_path = os.path.join(local_dir, rel_path)
#             ensure_local_dir(os.path.dirname(local_path))
#             t0 = time.time()
#             sys.stdout.write(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Downloading {rel_path}...') 
#             sys.stdout.flush()                 
#             sftp.get(remote_path, local_path)
#             transfer_speed = round((os.path.getsize(local_path) / (1024 * 1024)) / (time.time() - t0), 2)            
#             sys.stdout.write(f' done in {(time.time() - t0)/60:.2f} mins ({transfer_speed}MB/s)\n')            
#     sftp.close()
#     ssh.close()

def sync_updated_files_from_remote(remote_dir, local_dir):
    host, port, username, key_path = organise_paths.get_ssh_settings()

    # Convert local Windows path to WSL-style
    local_dir = Path(local_dir).resolve()
    local_path_wsl = str(local_dir).replace(":", "").replace("\\", "/")
    local_path_wsl = f"/mnt/{local_path_wsl[0].lower()}{local_path_wsl[1:]}/"

    # Build rsync command
    rsync_cmd = (
        f'wsl rsync -az --quiet -e "ssh -i {key_path} -p {port}" '
        f'{username}@{host}:"{remote_dir}/" "{local_path_wsl}"'
    )

    print(f"Running: {rsync_cmd}\n")

    # Run rsync
    subprocess.run(rsync_cmd, shell=True, check=True)

def delete_remote_file(remote_file_path):
    host, port, username, key_path = organise_paths.get_ssh_settings()
    key = Ed25519Key.from_private_key_file(key_path)
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(hostname=host, port=port, username=username, pkey=key)
    sftp = ssh.open_sftp()

    try:
        sftp.remove(remote_file_path)
        print(f"Deleted remote file: {remote_file_path}")
    except FileNotFoundError:
        print(f"File not found on remote: {remote_file_path}")

    sftp.close()
    ssh.close()
