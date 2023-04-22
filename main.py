import os

import pandas as pd
from BlindSpotClipper import BlindSpotClipper
from FrontAlertsClipper import FrontAlertsClipper
import shutil
import time
import paramiko

copy_files = True

camera = "Back"  # Back, Front
alerts_filename_rear = r"J:\BackAlerts.csv"
alerts_filename_front = r"J:\FrontAlerts.csv"

video_path = r"J:\Videos"
free_text = "Jakarta"

indices_filename = r"J:\New_Alerts\indices.csv"
indices_df = pd.read_csv(indices_filename)
Out_folder = r"J:\New_Alerts"

n_files = 0
max_files = 400
copy_files = False

if copy_files:
    Video_folder = r"I:\Videos\New Rides\Box 09"
    Video_folder_Out = r"I:\Videos\New Rides\Done\Box 09"
    destination_dir = r"J:\Videos"

    for item in os.listdir(Video_folder):
        folder = os.path.join(Video_folder, item)
        if not os.path.isdir(folder):
            continue

        dump_folder = os.path.join(folder, "dump")
        if not os.path.exists(dump_folder):
            continue

        print(f"{dump_folder}:")

        for file in os.listdir(dump_folder):
            src_file = os.path.join(dump_folder, file)
            shutil.copy(src_file, destination_dir)
            n_files = n_files + 1

            filename = os.path.basename(src_file)
            print(f"    {filename}")

        if not os.path.exists(Video_folder_Out):
            os.makedirs(Video_folder_Out)

        shutil.move(folder, Video_folder_Out)

        if n_files > max_files:
            print(f"stopping after max: {n_files} files")
            break

    print("finished copying")

    hostname = '192.168.0.100'
    username = 'rider'
    password = 'Rider2021'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)
# Back
    stdin, stdout, stderr = ssh.exec_command('cd ~/riderdome && ./rider_jetson -batch_back \"/home/rider/riderdome/Videos/*rear*.mp4\"')

    while not stdout.channel.exit_status_ready():
        str = stdout.read(64)
        print(str.decode('utf-8'), end='')
        time.sleep(0.1)

    # Front
    # stdin, stdout, stderr = ssh.exec_command('cd ~/riderdome && ./rider_jetson -batch_front \"/media/rider/6575-F30A1/Front_Alerts/*.mp4\"')
    stdin, stdout, stderr = ssh.exec_command('cd ~/riderdome && ./rider_jetson -batch_front \"/home/rider/riderdome/Videos/*front*.mp4\"')

    while not stdout.channel.exit_status_ready():
        str = stdout.read(64)
        print(str.decode('utf-8'), end='')
        time.sleep(0.1)

    ssh.close()

BlindSpotClipper(indices_filename, alerts_filename_rear, indices_df, os.path.join(Out_folder, "Back"), free_text, video_path)

FrontAlertsClipper(indices_filename, alerts_filename_front, indices_df, os.path.join(Out_folder, "Front"), free_text, video_path)

print("all done")
