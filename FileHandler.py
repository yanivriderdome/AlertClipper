import os

import paramiko


def get_file_indices(front_path, back_path, Out_folder):
    hostname = '192.168.0.100'
    username = 'rider'
    password = 'Rider2021'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)

    stdin, stdout, stderr = ssh.exec_command('ls ' + front_path)

    filenames_front = stdout.read()
    filenames_front = filenames_front.decode('utf-8')
    filenames_front = filenames_front.split("\n")
    filenames_front = [filename for filename in filenames_front if "False" not in filename]

    stdin, stdout, stderr = ssh.exec_command('ls ' + back_path)

    filenames_back = stdout.read()
    filenames_back = filenames_back.decode('utf-8')
    filenames_back = filenames_back.split("\n")
    filenames_back = [filename for filename in filenames_back if "False" not in filename and "Spot_Marginal" not in filename]

    for root, dirs, files in os.walk(Out_folder):
        for directory in dirs:
            new_files = os.listdir(os.path.join(Out_folder, directory))
            filenames_front = filenames_front + [str(filename) for filename in new_files
                                                 if "false" not in str(filename).lower() and
                                                 "front" in str(filename).lower()]
            filenames_back = filenames_back + [str(filename) for filename in new_files
                                                if "false" not in str(filename).lower() and
                                                "blind" in str(filename).lower()]
    indices = {'Left_Blind_Spot': 0, 'Right_Blind_Spot': 0, 'Bike_Left_Blind_Spot': 0, 'Bike_Right_Blind_Spot': 0,
               'Left_And_Right_Blind_Spot': 0, 'Bike_Left_And_Right_Blind_Spot': 0, 'Front_Collision': 0,
               'Front_Distance': 0, 'Front_Collision_Truck': 0,
               'Front_Distance_Truck': 0, 'Front_Collision_Bike': 0,
               'Front_Distance_Bike': 0, 'Front_Collision_Bus': 0,
               'Front_Distance_Bus': 0, 'Front_Collision_Traffic': 0,
               'Front_Distance_Traffic': 0, 'Front_Collision_Night': 0}
    for name_type in indices:
        print("getting file index for", name_type)
        if "Blind" in name_type:
            filenames = filenames_back
        else:
            filenames = filenames_front
        filenames = [filename for filename in filenames if filename.startswith(name_type)]
        numbers = [filename[len(name_type) + 1:].lstrip().split("_")[0] for filename in filenames]
        if len(numbers) > 0:
            indices[name_type] = 1 + max([int(number) for number in numbers if number.isdigit()])
    return indices
