import pandas as pd
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
from moviepy.video.compositing.concatenate import concatenate_videoclips
import math
import numpy as np
from BlindSpotClipper import get_alert_label, file_is_unique, vehicles
import shutil

inds_falses = {}


def get_output_filename(alert_types, classes, ids, scores, filename, alert_label, free_text, Out_folder, indices):
    if alert_label:
        classes = [_class for _score, _class in zip(scores, classes) if _score > 0.6]
        ids = [_id for _score, _id in zip(scores, ids) if _score > 0.6]
    alert_types = list(set(alert_types))
    alert_type = alert_types[0]

    if len(alert_types) == 1:
        alert_type = alert_types[0]
    alert_type = alert_type.replace("Safe", "Front")

    if len(classes) > 0 and np.unique(classes)[0] == 3:
        alert_type = alert_type + "_Bike"
    ids = list(set(ids))
    out_filename = alert_type.replace("Safe", "Front")

    traffic = len(ids) > 3

    if alert_label:
        out_filename = out_filename + "_{:04d}".format(indices[alert_type])
        indices[alert_type] += 1
    else:
        out_filename = out_filename + "_False" + "_"

    out_filename = out_filename + "_" + free_text

    if traffic:
        out_filename = out_filename + "_Traffic"
    elif len(classes) > 0 and classes[0] > 1 and classes[0] != 3:
        out_filename = out_filename + "_" + vehicles[classes[0]]

    if not alert_label:
        if filename not in inds_falses:
            inds_falses[filename] = 1
        else:
            inds_falses[filename] = inds_falses[filename] + 1
            out_filename = out_filename + "_" + str(inds_falses[filename])


    out_filename = out_filename + "_" + filename
    out_filename = out_filename.replace("buss", "busses")
    out_filename = out_filename.replace("__", "_")
    out_filename = out_filename.replace("Front_Distance_False_", "Front_False_")
    out_filename = out_filename.replace("Front_Collision_False_", "Front_False_")
    print("saving", out_filename)
    return os.path.join(Out_folder, out_filename), indices


def correct_data(data):
    for i, line in enumerate(data):
        if line['file0'] == line['file1'] and abs(line['ind0'] - line['ind1']):
            if line['ind0'] > 200:
                line['ind0'] = 0
            else:
                line['ind1'] = min(line['ind1'] + 200, 800)
        if 'Safe_Distance' in line['Alert Types'] and 'Front_Collision' in line['Alert Types']:
            indices = list(np.where(np.asarray(line['Alert Types']) == 'Front_Collision')[0])
            collision_scores = [line['scores'][x] for x in indices]
            if max(collision_scores) > 0.6:
                line['Alert Types'] = ['Front_Collision' for _ in line['Alert Types']]
            else:
                line['Alert Types'] = ['Safe_Distance' for _ in line['Alert Types']]
        data[i] = line
    return data


def FrontAlertsClipper(filename, indices, Out_folder, free_text, video_path):
    # dump_df = pd.read_csv(filename.replace("Alerts", "Data"))
    if not os.path.exists(filename):
        print("No Front Alerts Filename")
        return
    alerts_df = pd.read_csv(filename)
    alerts_df = alerts_df[alerts_df["ClassifierResult"] > 0.4]
    ids = alerts_df["Id"].unique()

    data = []
    data_log = []
    prev_data = {"file0": "_",
                 "ind0": 0,
                 "file1": "_",
                 "ind1": 0}
    min_video_length = 250
    df_scores = alerts_df.groupby("Id")["ClassifierResult"].max()

    for value in ids:
        min_index = alerts_df.loc[alerts_df['Id'] == value].index.min()
        max_index = alerts_df.loc[alerts_df['Id'] == value].index.max()
        id = alerts_df["Id"][max_index]
        score = alerts_df[alerts_df["Id"] == id]["ClassifierResult"].max()
        new_data = {"file0": alerts_df["FirstAppearedFile"][min_index],
                    "ind0": alerts_df["FirstAppearedFrameNumber"][min_index],
                    "file1": alerts_df["Black Box Filename"][max_index],
                    "ind1": alerts_df["Black Box Frame Number"][max_index],
                    "ids": [id],
                    "Classes": [alerts_df["Class"][max_index]],
                    "Alert Types": [alerts_df["Alert Type"][max_index]],
                    "scores": [score]}
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

        new_data["alert_label"] = get_alert_label(alerts_df, new_data, df_scores)

        if prev_data["file1"] == new_data["file0"] and new_data["ind0"] - prev_data["ind1"] < 30:
            data[-1]["file1"] = new_data["file1"]
            data[-1]["ind1"] = new_data["ind1"]
            data[-1]["Alert Types"].append(alerts_df["Alert Type"][max_index])
            data[-1]["Classes"].append(alerts_df["Class"][max_index])
            data[-1]["ids"].append(alerts_df["Id"][max_index])
            data[-1]["scores"].append(score)
        else:
            data.append(new_data)
            prev_data = new_data.copy()
    i = 0

    data = correct_data(data)
    inds_to_skip = []
    for i, line in enumerate(data[1:]):
        if line['file0'] == data[i-1]['file0'] and abs(line['ind0'] - data[i-1]['ind0']) < 100:
            line['ind0'] = min(line['ind0'],data[i-1]['ind0'])
            inds_to_skip.append(i-1)
    for line in data:
        input_filename1 = os.path.join(video_path, line["file0"])
        if not os.path.exists(input_filename1):
            print(input_filename1, " not found!")
            continue
        start_frame1 = line["ind0"]
        video1 = VideoFileClip(input_filename1)
        alert_label = get_alert_label(alerts_df, line, df_scores)
        out_filename, indices = get_output_filename(line["Alert Types"], line["Classes"], line["ids"],
                                                    line["scores"],
                                                    line["file0"], alert_label,
                                                    free_text, Out_folder, indices)

        if not alert_label and file_is_unique(line["file0"], data):
            shutil.copy(input_filename1, out_filename)
            continue

        try:
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
                # duration2 = video2.duration

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
                final_video.close()

            data_log.append({"Filename": out_filename, "Type": line["Alert Types"][0],
                             "Start Frame": line["ind0"], "Start File": line["file0"],
                             "End Frame": line["ind1"], "End File": line["file0"]})
        except:
            continue
    out_df = pd.json_normalize(data_log)
    out_df.to_csv("LogBack.csv")
