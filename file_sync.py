import os
import time
from paramiko import SSHClient, Ed25519Key, AutoAddPolicy
import stat
import organise_paths  # assumes this module exists and provides get_ssh_settings()

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
    key = Ed25519Key.from_private_key_file(key_path)
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(hostname=host, port=port, username=username, pkey=key)
    sftp = ssh.open_sftp()

    local_dirs = list_local_dirs(local_dir)
    remote_dirs = set(list_remote_dirs(sftp, remote_dir))

    for rel_dir in local_dirs:
        if rel_dir not in remote_dirs:
            remote_path = f"{remote_dir}/{rel_dir}".replace("\\", "/")
            ensure_remote_dir(sftp, remote_path)
            print(f"Creating remote folder: {rel_dir}")

    local_files = list_local_files(local_dir)
    remote_files = list_remote_files(sftp, remote_dir)

    for rel_path, (local_mtime, local_size) in local_files.items():
        remote_info = remote_files.get(rel_path)
        should_upload = (
            remote_info is None or
            local_mtime > remote_info[0] or
            local_size != remote_info[1]
        )
        if should_upload:
            local_path = os.path.join(local_dir, rel_path)
            remote_path = f"{remote_dir}/{rel_path}".replace("\\", "/")
            ensure_remote_dir(sftp, os.path.dirname(remote_path))
            print(f"Uploading {rel_path}...")
            sftp.put(local_path, remote_path)

    sftp.close()
    ssh.close()

def sync_updated_files_from_remote(remote_dir, local_dir):
    host, port, username, key_path = organise_paths.get_ssh_settings()
    key = Ed25519Key.from_private_key_file(key_path)
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(hostname=host, port=port, username=username, pkey=key)
    sftp = ssh.open_sftp()

    local_dirs = set(list_local_dirs(local_dir))
    remote_dirs = list_remote_dirs(sftp, remote_dir)

    for rel_dir in remote_dirs:
        if rel_dir not in local_dirs:
            local_path = os.path.join(local_dir, rel_dir)
            ensure_local_dir(local_path)
            print(f"Creating local folder: {rel_dir}")

    local_files = list_local_files(local_dir)
    remote_files = list_remote_files(sftp, remote_dir)

    for rel_path, (remote_mtime, remote_size) in remote_files.items():
        local_info = local_files.get(rel_path)
        should_download = (
            local_info is None or
            remote_mtime > local_info[0] or
            remote_size != local_info[1]
        )
        if should_download:
            remote_path = f"{remote_dir}/{rel_path}".replace("\\", "/")
            local_path = os.path.join(local_dir, rel_path)
            ensure_local_dir(os.path.dirname(local_path))
            print(f"Downloading {rel_path}...")
            sftp.get(remote_path, local_path)

    sftp.close()
    ssh.close()

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
