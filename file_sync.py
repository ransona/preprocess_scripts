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

def sync_updated_files_from_remote(remote_dir, local_dir):
    host, port, username, key_path = organise_paths.get_ssh_settings()

    # Convert local Windows path to WSL-style
    local_dir = Path(local_dir).resolve()
    # make dir if doesn't exist
    local_dir.mkdir(parents=True, exist_ok=True)
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
