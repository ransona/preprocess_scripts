# script to clone experiments between users
import os
import shutil
import pwd
import grp
import organise_paths

expID = '2023-04-20_03_ESMT124'

source_user = 'melinatimplalexi'
dest_user = 'adamranson'

[_, _, _, exp_dir_processed_source, _] = organise_paths.find_paths(source_user, expID)
[_, _, _, exp_dir_processed_dest, _] = organise_paths.find_paths(dest_user, expID)


def copy_files(src_dir, dst_dir, username):
    # Get the uid and gid from the username
    uid = pwd.getpwnam(username).pw_uid
    gid = grp.getgrnam(username).gr_gid

    for dirpath, dirnames, filenames in os.walk(src_dir):
        # Create the destination directory structure
        structure = os.path.join(dst_dir, os.path.relpath(dirpath, src_dir))
        if not os.path.isdir(structure):
            os.makedirs(structure, exist_ok=True)
            os.chown(structure, uid, gid)

        # Copy the files
        for file in filenames:
            src_file = os.path.join(dirpath, file)
            dst_file = os.path.join(structure, file)
            print(f'Copying file {os.path.basename(src_file)}')
            shutil.copy2(src_file, dst_file)  # copy2 preserves file metadata
            os.chown(dst_file, uid, gid)  # change the owner and group


# Usage
copy_files(exp_dir_processed_source, exp_dir_processed_dest, dest_user)
