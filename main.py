import pandas as pd
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
from moviepy.video.compositing.concatenate import concatenate_videoclips
import math

vehicles = {-1: "Unknown", 0: "Car", 1: "Bus", 2: "Truck", 3: "Bike"}
names_dict = {"Right BlindSpot": {3: "Bike_Blind_Spot_Right_", 0: "Right_Blind_Spot_"},
              "Left BlindSpot": {3: "Bike_Blind_Spot_Left_", 0: "Left_Blind_Spot_"},
              "Both BlindSpots": {3: "Bike_Blind_Spot_Left_And_Right_", 0: "Blind_Spots_"}}

indices_filename = "indices.csv"
indices_df = pd.read_csv(indices_filename)
Out_folder = "Videos"

inds_falses = {}


def get_output_filename(alert_types, classes, ids, filename, alert_label, free_text):
    alert_types = list(set(alert_types))
    alert_type = alert_types[0]
    if "Left BlindSpot" in alert_types and "Right BlindSpot" in alert_types:
        alert_type = "Both BlindSpots"
    if len(alert_types) == 1:
        alert_type = alert_types[0]
    classes_unique = list(set(classes))
    ids = list(set(ids))
    if len(classes_unique) == 0:
        out_filename = names_dict[alert_type][classes_unique[0]]
    else:
        out_filename = names_dict[alert_type][0]
    if alert_label:
        out_filename = out_filename + "{:04d}".format(indices_df[alert_type][0])
        indices_df[alert_type][0] = indices_df[alert_type][0] + 1
    else:
        out_filename = out_filename.replace("Blind_Spots_", "Blind_Spot_")
        out_filename = out_filename + "_False" + "_"

    if len(ids) == 1:
        if classes_unique[0] != -1:
            out_filename = out_filename + "_" + vehicles[classes_unique[0]]
    else:
        if len(classes_unique) == 1:
            out_filename = out_filename + "_" + str(len(ids)) + "_" + vehicles[classes_unique[0]] + "s"
        else:
            counts = {}
            for item in classes:
                if item in counts:
                    counts[item] += 1
                else:
                    counts[item] = 1
            vehicle_names = [
                "_" + vehicles[item] if counts[item] == 1 else "_" + str(counts[item]) + "_" + vehicles[item] + "s" for
                item in counts]
            out_filename = out_filename + "_".join(vehicle_names)
    if not alert_label:
        if filename not in inds_falses:
            inds_falses[filename] = 1
        else:
            inds_falses[filename] = inds_falses[filename] + 1
            out_filename = out_filename + "_" + inds_falses[filename]

    out_filename = out_filename + "_" + free_text + "_" + filename
    out_filename = out_filename.replace("buss", "busses")
    out_filename = out_filename.replace("__", "_")
    print("saving", out_filename)
    return os.path.join(Out_folder, out_filename)


filename = "BackAlerts.csv"
video_path = r"D:\Videos2"

dump_df = pd.read_csv(filename.replace("Alerts", "Data"))
alerts_df = pd.read_csv(filename)
alerts_df = alerts_df[alerts_df["ClassifierResult"] > 0.4]
ids = alerts_df["Id"].unique()
data = []
prev_data = {"file0": "_",
             "ind0": 0,
             "file1": "_",
             "ind1": 0}
min_video_length = 100
df_scores = alerts_df.groupby("Id")["ClassifierResult"].max()

for value in ids:
    min_index = dump_df.loc[dump_df['Id'] == value].index.min()
    max_index = alerts_df.loc[alerts_df['Id'] == value].index.max()
    new_data = {"file0": dump_df["Black Box Filename"][min_index],
                "ind0": dump_df["Black Box Frame Number"][min_index],
                "file1": alerts_df["Black Box Filename"][max_index],
                "ind1": alerts_df["Black Box Frame Number"][max_index],
                "ids": [alerts_df["Id"][max_index]],
                "Classes": [alerts_df["Class"][max_index]],
                "Alert Types": [alerts_df["Alert Type"][max_index]]}
    if "blind" in new_data["Alert Types"][0].lower():
        if alerts_df["AbsAngle"][max_index] < 50:
            new_data["ind1"] = max(new_data["ind1"], min(new_data["ind1"] + 50, 800))
        # pass
    while new_data["file0"] == new_data["file1"] and new_data["ind1"] - new_data["ind0"] < min_video_length:
        new_data["ind0"] = max(int(new_data["ind0"]) - 60, 0)
        if new_data["ind0"] == 0:
            break
    if len(data) > 1:
        prev_data = data[-1]
    if prev_data["file1"] == new_data["file0"] and new_data["ind0"] - prev_data["ind1"] < 30:
        data[-1]["file1"] = new_data["file1"]
        data[-1]["ind1"] = new_data["ind1"]
        data[-1]["Alert Types"].append(alerts_df["Alert Type"][max_index])
        data[-1]["Classes"].append(alerts_df["Class"][max_index])
        data[-1]["ids"].append(alerts_df["Id"][max_index])
    else:
        data.append(new_data)
df = pd.DataFrame(data)
i = 0

for line in data:
    input_filename1 = os.path.join(video_path, line["file0"])
    start_frame1 = line["ind0"]
    video1 = VideoFileClip(input_filename1)
    # scores = [df_scores[id] for id in line["ids"]]
    df_ind1 = alerts_df.loc[
        (alerts_df['Black Box Filename'] == line["file0"]) & (alerts_df['Id'] == line["ids"][0])].index.min()
    if math.isnan(df_ind1):
        df_ind1 = alerts_df.loc[(alerts_df['Black Box Filename'] == line["file0"])].index.min()

    df_ind2 = alerts_df.loc[
        (alerts_df['Black Box Filename'] == line["file1"]) & (alerts_df['Id'] == line["ids"][-1])].index.max()
    if math.isnan(df_ind2):
        df_ind2 = alerts_df.loc[(alerts_df['Black Box Filename'] == line["file1"])].index.max()
    scores = alerts_df["ClassifierResult"][df_ind1:df_ind2]
    scores2 = [df_scores[id] for id in line["ids"]]
    alert_label = True
    if (len(scores) > 0 and max(scores) < 0.7) or (len(scores2) > 0 and max(scores2) < 0.7):
        alert_label = False
    out_filename = get_output_filename(line["Alert Types"], line["Classes"], line["ids"], line["file0"], alert_label,
                                       "Jakarta")

    if line["file0"] == line["file1"]:
        end_frame1 = line["ind1"]
        start_time = start_frame1 / video1.fps
        end_time = end_frame1 / video1.fps

        # cut the video between the start and end times
        cut_video = video1.subclip(start_time, end_time)

        # write the cut video to a new file
        cut_video.write_videofile(out_filename, fps=30)
        i = i + 1
    else:
        input_filename2 = os.path.join(video_path, line["file1"])
        video2 = VideoFileClip(input_filename2)

        # get the duration of the videos in seconds
        duration1 = video1.duration
        duration2 = video2.duration

        # calculate the start and end times for the cut videos
        start_time1 = line["ind0"] / video1.fps
        end_time1 = duration1

        start_time2 = 0
        end_time2 = line["ind1"] / video2.fps

        # cut the videos between the start and end times
        cut_video1 = video1.subclip(start_time1, end_time1)
        cut_video2 = video2.subclip(start_time2, end_time2)

        # concatenate the cut videos into one video
        final_video = concatenate_videoclips([cut_video1, cut_video2])

        # write the final video to a new file
        final_video.write_videofile(out_filename, fps=30)
indices_df.to_csv(indices_filename)
