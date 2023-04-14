import os

import pandas as pd
from BlindSpotClipper import BlindSpotClipper
from FrontAlertsClipper import FrontAlertsClipper
import shutil
import paramiko


copy_files = False

camera = "Back"
alerts_filename = r"J:\BackAlerts.csv"
if camera == "Front":
    alerts_filename = r"J:\FrontAlerts.csv"

video_path = r"J:\Videos"
free_text = "Jakarta"

indices_filename = "indices.csv"
indices_df = pd.read_csv(indices_filename)
Out_folder = "Videos"


if copy_files:
    Video_folder = r"I:\Videos\New Rides\Box 09"
    Video_folder_Out = r"I:\Videos\New Rides\Done\Box 09"
    destination_dir = r"J:\Videos"

    max_files = 200
    n_files = 0
    for item in os.listdir(Video_folder):
        folder = os.path.join(Video_folder, item)
        if not os.path.isdir(folder):
            continue
        dump_folder = os.path.join(folder, "dump")
        if not os.path.exists(dump_folder):
            continue
        for file in os.listdir(dump_folder):
            src_file = os.path.join(dump_folder, file)
            shutil.copy(src_file, destination_dir)
        n_files = n_files + len(os.listdir(dump_folder))
        if not os.path.exists(Video_folder_Out):
            os.makedirs(Video_folder_Out)

        shutil.move(folder, Video_folder_Out)
        if n_files > max_files:
            break
    print("finished copying")
    hostname = '192.168.0.100'
    username = 'rider'
    password = 'Rider2021'

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(hostname, username=username, password=password)
    # stdin, stdout, stderr = ssh_client.exec_command('ls')
    stdin, stdout, stderr = ssh_client.exec_command('./rider_jetson -batch_front /media/rider/6575-F30A1/Front\ Alerts/*.mp4 -first_file 0')
    while not stdout.channel.exit_status_ready():
        # Do something else while waiting for the command to finish
        # For example, you can print some message
        print('Waiting for script to finish...')

    # Print the command output
    print(stdout.read().decode('utf-8'))

    # Close the SSH connection
    ssh_client.close()

else:
    if camera == "Front":
        FrontAlertsClipper(indices_filename, alerts_filename, indices_df, Out_folder, free_text, video_path)
    else:
        BlindSpotClipper(indices_filename, alerts_filename, indices_df, Out_folder, free_text, video_path)