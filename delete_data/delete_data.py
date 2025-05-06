import os
import shutil

# Repository path
repository_folder = "/home/adamranson/temp/delete_test"

def load_ids(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    with open(file_path, 'r') as f:
        return f.read().splitlines()

def delete_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)
        print(f"[INFO] Deleted: {path}")
    else:
        print(f"[INFO] Does not exist: {path}")

def is_empty_dir(path):
    return os.path.isdir(path) and not os.listdir(path)

if __name__ == "__main__":
    # Load and delete animal folders from animalIDs.txt
    animal_ids = load_ids("animalIDs.txt")
    for animal in animal_ids:
        animal_path = os.path.join(repository_folder, animal)
        delete_folder(animal_path)

    # Load and delete experiment folders from expIDs.txt
    exp_ids = load_ids("expIDs.txt")

    for exp_id in exp_ids:
        if len(exp_id) > 14:
            animal_id = exp_id[14:]
            exp_path = os.path.join(repository_folder, animal_id, exp_id)
            delete_folder(exp_path)

            # After deleting exp folder, check if the animal folder is empty
            animal_path = os.path.join(repository_folder, animal_id)
            if is_empty_dir(animal_path):
                print(f"[INFO] {animal_path} is empty after deleting {exp_id}. Deleting animal folder.")
                delete_folder(animal_path)
            else:
                print(f"[INFO] {animal_path} is not empty after deleting {exp_id}.")
