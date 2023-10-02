import os

from BlindSpotClipper import BlindSpotClipper
from FrontAlertsClipper import FrontAlertsClipper
from FileHandler import get_file_indices
import shutil
import time
import paramiko

Folder = "Box 14"

Video_folder = os.path.join(r"I:\Videos\New_Rides", Folder)
Video_folder_Out = os.path.join(r"I:\Videos\New_Rides\2023_Done", Folder)

free_text = "Singapore"


alerts_filename_rear = r"J:\BackAlerts.csv"
alerts_filename_front = r"J:\FrontAlerts.csv"
video_path = r"J:\Videos"
Out_folder = r"J:\New_Alerts"


max_files = 200
copy_files = False
Run_Jetson_App = False


n_files = 0
if copy_files:
    destination_dir = r"J:\Videos"
    if not os.path.exists(destination_dir):
        os.mkdir(destination_dir)
    for file in os.listdir(destination_dir):
        if 'mp4' in file:
            os.remove(os.path.join(destination_dir, file))

    for item in os.listdir(Video_folder):
        folder = os.path.join(Video_folder, item)
        if not os.path.isdir(folder):
            continue

        dump_folder = os.path.join(folder, "dump")
        if not os.path.exists(dump_folder):
            continue

        print(f"{dump_folder}:")
        if os.path.exists(os.path.join(Video_folder_Out, item)):
            print("Folder ", item, " Exists in output folder. Skipping")
            continue
        for file in os.listdir(dump_folder):
            src_file = os.path.join(dump_folder, file)
            if "0000" in src_file:
                filename = os.path.basename(src_file)  # Get the folder name
                folder_name = os.path.dirname(src_file).split("\\")[-2]
                new_filename = f"{folder_name}_{filename}"  # Create the new filename

                new_path = src_file.replace(filename, new_filename)

                os.rename(src_file, new_path)
                src_file = new_path

            shutil.copy(src_file, destination_dir)
            n_files = n_files + 1

            filename = os.path.basename(src_file)
            print(f"{filename}")

        if not os.path.exists(Video_folder_Out):
            os.makedirs(Video_folder_Out)

        shutil.move(folder, Video_folder_Out)

        if n_files > max_files:
            print(f"stopping after max: {n_files} files")
            break

    print("finished copying")

if n_files > 0 or not copy_files:
    if Run_Jetson_App:
        if os.path.exists(r"J:\BackAlerts.csv"):
            os.remove(r"J:\BackAlerts.csv")
        if os.path.exists(r"J:\FrontAlerts.csv"):
            os.remove(r"J:\FrontAlerts.csv")

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

    indices = get_file_indices('/media/rider/4689-5BB2/Front_Alerts/', '/media/rider/6575-F30A2/Blindspot_All/',
                               Out_folder)
    #
    BlindSpotClipper(alerts_filename_rear, indices, os.path.join(Out_folder, "Back"), free_text,
                     video_path)

    # Front
    if Run_Jetson_App:
        stdin, stdout, stderr = ssh.exec_command('cd ~/riderdome && ./rider_jetson -batch_front \"/home/rider/riderdome/Videos/*front*.mp4\"')

        while not stdout.channel.exit_status_ready():
            str = stdout.read(64)
            print(str.decode('utf-8'), end='')
            time.sleep(0.1)

        ssh.close()

    # FrontAlertsClipper(alerts_filename_front, indices, os.path.join(Out_folder, "Front"), free_text, video_path)

    print("all done")
else:
    print("folder is empty")
