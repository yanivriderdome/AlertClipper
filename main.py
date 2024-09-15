import os
import re
from BlindSpotClipper import BlindSpotClipper
from FrontAlertsClipper import FrontAlertsClipper
from FileHandler import get_file_indices, delete_previous_csv_files, run_jetson_app
import shutil

Folder = "Yoav"
free_text = "Israel"

copy_files = False
Run_Jetson_App = False

Video_folder = os.path.join(r"I:\Videos\New_Rides", Folder)
Video_folder_Out = os.path.join(r"I:\Videos\New_Rides\2024_Done", Folder)

BlindSpots_filename = r"J:\BlindSpots.csv"
Front_Collision_filename = r"J:\FrontCollision.csv"
Safe_Distance_filename = r"J:\SafeDistance.csv"

video_path = r"J:\Videos"
Out_folder = r"I:\Videos\New_Alerts"
max_files = 300

n_files = 0
if copy_files:
    destination_dir = r"J:\Videos"
    if os.path.exists(destination_dir):
        [os.remove(os.path.join(destination_dir, file)) for file in os.listdir(destination_dir)]
    else:
        os.mkdir(destination_dir)

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

        shutil.move(folder, Video_folder_Out)

        if n_files > max_files:
            print(f"stopping after max: {n_files} files")
            break

        print("finished copying")

indices = get_file_indices('/media/rider/4689-5BB2/Front_Alerts/', '/media/rider/6575-F30A2/Blindspot_All/',
                           Out_folder)
if Run_Jetson_App:
    delete_previous_csv_files()
    run_jetson_app('cd ~/riderdome && ./rider_jetson -batch_back \"/home/rider/riderdome/Videos/*rear*.mp4\" -LogAlertFeatures 1')
BlindSpotClipper(BlindSpots_filename, indices, os.path.join(Out_folder, "New"), free_text, video_path)
#
# Front
if Run_Jetson_App:
    run_jetson_app('cd ~/riderdome && ./rider_jetson -batch_front \"/home/rider/riderdome/Videos/*front*.mp4\" -LogAlertFeatures 1')

FrontAlertsClipper(Front_Collision_filename, indices, os.path.join(Out_folder, "New"), free_text, video_path)
FrontAlertsClipper(Safe_Distance_filename, indices, os.path.join(Out_folder, "New"), free_text, video_path)

print("all done")
