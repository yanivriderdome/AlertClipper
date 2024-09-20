import pandas as pd
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
from moviepy.video.compositing.concatenate import concatenate_videoclips
import math
import shutil
import cv2

vehicles = {-1: "Unknown", 0: "Car", 1: "Bus", 2: "Truck", 3: "Bike"}

inds_falses = {}

from moviepy.video.io.VideoFileClip import VideoFileClip

# List to hold all opened VideoFileClip objects
opened_videos = []

def open_video(filename):
    video_clip = VideoFileClip(filename)
    opened_videos.append(video_clip)

def close_all_videos():
    for video_clip in opened_videos:
        video_clip.close()


def is_night(filename):
    if "0000" in filename:
        return False
    if not "_" in filename:
        return False
    parsed_filename = filename.split("_")
    time = parsed_filename[1]
    hour = time.split(".")[0]
    if not hour.isdigit():
        return False
    hour = int(hour)
    if hour > 19:
        return True
    return False


def get_previous_filename(video_path, current_file, alert_name):
    files = os.listdir(video_path)
    index = files.index(current_file)
    if index < 2:
        return current_file
    else:
        new_file = files[index - 2]
        if "blind" in alert_name.lower() and "rear" in new_file:
            return new_file
        if "rear" in files[index + 1]:
            return files[index - 1]
        if "rear" in files[index - 1]:
            return files[index - 1]
        return current_file


def get_output_filename(alert_types, classes, ids, scores, n_cars, filename, alert_label, free_text, out_folder,
                        indices):
    alert_types = list(set(alert_types))
    alert_types = [alert_type.replace(" ", "_").replace("BlindSpot", "Blind_Spot") for alert_type in alert_types]
    alert_type = alert_types[0]
    if "Left_Blind_Spot" in alert_types and "Right_Blind_Spot" in alert_types:
        alert_type = "Left_And_Right_Blind_Spot"
    classes_unique = list(set(classes))

    if max(scores) < 0.6 and alert_label == 1:
        alert_label = -1

    if max(scores) < 0.5:
        alert_label = 0

    if alert_label == 1:
        classes = [_class for _score, _class in zip(scores, classes) if _score > 0.7]
        ids = [_id for _score, _id in zip(scores, ids) if _score > 0.7]
        ids = list(set(ids))

        if classes_unique == [3] and "Blind" in alert_type:
            alert_type = "Bike_" + alert_type

    if alert_label == -1:
        classes = [_class for _score, _class in zip(scores, classes) if _score > 0.6]
        ids = [_id for _score, _id in zip(scores, ids) if _score > 0.6]
        ids = list(set(ids))

        if classes_unique == [3] and "Blind" in alert_type:
            alert_type = "Bike_" + alert_type

    out_filename = alert_type

    if alert_label == 1:
        out_filename = out_filename + "_{:04d}".format(indices[alert_type])
        indices[alert_type] += 1
    elif alert_label == -1:
        out_filename = out_filename + "_Marginal"
    else:
        indices[alert_type] += 1
        out_filename = out_filename.replace("Blind_Spots_", "Blind_Spot_") + "_False"

    out_filename = out_filename + "_" + free_text
    if is_night(filename):
        out_filename = out_filename + "_Night"
    if n_cars[0] + n_cars[1] > 3:
        out_filename = out_filename + "_Traffic"

    if not out_filename.startswith("Bike_"):
        if len(ids) == 1:
            out_filename = out_filename + "_" + vehicles[classes_unique[0]]
        else:
            if len(classes_unique) == 1:
                out_filename = out_filename + "_" + str(len(ids)) + "_" + vehicles[classes_unique[0]] + "s"
            else:
                counts = {}
                if alert_label:
                    true_classes = [class_i for class_i, score in zip(classes, scores) if score > 0.7]
                    for item in true_classes:
                        if item in counts:
                            counts[item] += 1
                        else:
                            counts[item] = 1
                else:
                    for item in classes:
                        if item in counts:
                            counts[item] += 1
                        else:
                            counts[item] = 1

                if len(ids) > 1:
                    for item in classes:
                        if item in counts:
                            counts[item] += 1
                        else:
                            counts[item] = 1

                    vehicle_names = [
                        "_" + vehicles[item] if counts[item] == 1 else "_" + str(counts[item]) + "_" + vehicles[
                            item] + "s"
                        for
                        item in counts]
                    out_filename = out_filename + "_".join(vehicle_names)
    if not alert_label:
        if filename not in inds_falses:
            inds_falses[filename] = 1
        else:
            inds_falses[filename] = inds_falses[filename] + 1
            out_filename = out_filename + "_" + str(inds_falses[filename])

    out_filename = out_filename + "_" + filename
    out_filename = out_filename.replace("Buss", "Buses")
    out_filename = out_filename.replace("__", "_")
    print("saving", out_filename)
    return os.path.join(out_folder, out_filename), indices


def get_number(filename):
    if "_rear" in filename:
        filename = filename.split("_rear")[0]
        filename = filename.split(".")[-1]
    else:
        filename = filename.replace("cam1_", " ")
        filename = filename.split(".")[0]
    try:
        return int(filename)
    except:
        return -1


def get_alert_label(alerts_df, line, df_scores, score_column="ClassifierScore"):
    df_ind1 = alerts_df.loc[
        (alerts_df['Black Box Filename'] == line["file0"]) & (alerts_df['Id'] == line["ids"][0])].index.min()

    if math.isnan(df_ind1):
        df_ind1 = alerts_df.loc[(alerts_df['Black Box Filename'] == line["file0Orig"])].index.min()

    df_ind2 = alerts_df.loc[
        (alerts_df['Black Box Filename'] == line["file1"]) & (alerts_df['Id'] == line["ids"][-1])].index.max()
    if math.isnan(df_ind1):
        return -1
    if math.isnan(df_ind2):
        df_ind2 = alerts_df.loc[(alerts_df['Black Box Filename'] == line["file1"])].index.max()
    try:
        scores = alerts_df[score_column][df_ind1:df_ind2]
    except ValueError:
        scores = []
    scores2 = [df_scores[id] for id in line["ids"]]
    if (len(scores) > 0 and max(scores) > 0.7) or (len(scores2) > 0 and max(scores2) > 0.7):
        return 1
    if (len(scores) > 0 and max(scores) > 0.6) or (len(scores2) > 0 and max(scores2) > 0.6):
        return -1

    return False


def video_too_short(new_data, min_video_length=200):
    return new_data["file0"] == new_data["file1"] and new_data["ind1"] - new_data["ind0"] < min_video_length


def file_is_unique(filename, data):
    for line in data:
        if not line["alert_label"]:
            continue
        if line["file0"] == filename or line["file1"] == filename:
            return False
    return True


def BlindSpotClipper(filename, indices, out_folder, free_text, video_path):
    if not os.path.exists(filename):
        print(filename, "not found!")
        return
    alerts_df = pd.read_csv(filename)
    alerts_df = alerts_df[alerts_df["ClassifierScore"] > 0.4]

    ids = alerts_df["Id"].unique()
    data_log = []
    data = []
    prev_data = {"file0": "_",
                 "ind0": 0,
                 "file1": "_",
                 "ind1": 0}
    min_video_length = 200
    df_scores = alerts_df.groupby("Id")["ClassifierScore"].max()

    for vehicle_id in ids:
        if len(data) > 1:
            prev_data = data[-1]

        min_index = alerts_df.loc[alerts_df['Id'] == vehicle_id].index.min()
        max_index = alerts_df.loc[alerts_df['Id'] == vehicle_id].index.max()
        score = df_scores[vehicle_id]
        new_data = {"file0": alerts_df["FirstAppearedFile"][min_index],
                    "file0Orig": alerts_df["FirstAppearedFile"][min_index],
                    "ind0": alerts_df["FirstAppearedFrameNumber"][min_index],
                    "file1": alerts_df["Black Box Filename"][max_index],
                    "ind1": alerts_df["Black Box Frame Number"][max_index],
                    "ids": [vehicle_id],
                    "Classes": [alerts_df["Class"][max_index]],
                    "Alert Types": [
                        alerts_df["Alert Type"][max_index].replace(" ", "_").replace("BlindSpot", "Blind_Spot")],
                    "NCarsLeft": [alerts_df["TrafficStatistics.NCarsLeft"][max_index]],
                    "NCarsRight": [alerts_df["TrafficStatistics.NCarsRight"][max_index]],
                    "scores": [score]}

        if "blind" in new_data["Alert Types"][0].lower() and alerts_df["AbsAngle"][max_index] < 50:
            new_data["ind1"] = max(new_data["ind1"], min(new_data["ind1"] + 50, 800))

        manual_cut = False

        while video_too_short(new_data, min_video_length):
            if new_data["ind0"] > 0:
                new_data["ind0"] = max(int(new_data["ind0"]) - 60, 0)
            else:
                new_file = get_previous_filename(video_path, new_data["file0"], new_data["Alert Types"][0])
                if new_file == new_data["file0"]:
                    break
                else:
                    new_data["file0"] = new_file
                    new_data["ind0"] = 700
                manual_cut = True
                break
        new_data["alert_label"] = get_alert_label(alerts_df, new_data, df_scores)

        if not manual_cut and prev_data["file1"] != "_" and (
                ((prev_data["file1"] == new_data["file0"] and new_data["ind0"] - prev_data["ind1"] < 120) or
                 ((('000' not in prev_data["file1"] and abs(
                     get_number(prev_data["file1"]) == get_number(new_data["file0"]) < 40)) or
                   ('000' in prev_data["file1"] and abs(
                       get_number(prev_data["file1"]) - get_number(new_data["file0"]) < 2))) and
                  abs(prev_data["ind1"] - 812) + new_data["ind0"] < 120))):
            if (max(new_data["scores"]) > 0.7) or \
                    (max(new_data["scores"]) < 0.7 and max(prev_data["scores"]) < 0.6):
                data[-1]["file1"] = new_data["file1"]
                data[-1]["ind1"] = new_data["ind1"]
                data[-1]["Alert Types"].append(alerts_df["Alert Type"][max_index])
                data[-1]["Classes"].append(alerts_df["Class"][max_index])
                data[-1]["ids"].append(alerts_df["Id"][max_index])
                data[-1]["scores"].append(score)
                data[-1]["alert_label"] = new_data["alert_label"]
                prev_data = data[-1].copy()
        else:
            data.append(new_data)
            prev_data = new_data.copy()
        if max(data[-1]["scores"]) < 0.7 and data[-1]["alert_label"] == 1:
            data[-1]["alert_label"] = -1

    for i in range(len(data[:-1])):
        if i >= len(data[:-1]) - 1:
            break
        current_clip = data[i]
        next_clip = data[i + 1]
        if current_clip["file0"] == next_clip["file0"] and current_clip["file1"] == next_clip["file1"]:
            for key in ['ids', 'Classes', 'Alert Types', 'scores']:
                current_clip[key] = current_clip[key] + next_clip[key]
            current_clip['ind0'] = min(current_clip['ind0'], next_clip['ind0'])
            current_clip['ind1'] = max(current_clip['ind1'], next_clip['ind1'])
            current_clip['alert_label'] = max(current_clip['alert_label'], next_clip['alert_label'])
            del (data[i])

        if current_clip["file0"] == next_clip["file0"] and not \
                (current_clip["file1"] == current_clip["file0"] and next_clip["ind1"] > current_clip["ind0"]):
            for key in ['ids', 'Classes', 'Alert Types', 'scores']:
                current_clip[key] = current_clip[key] + next_clip[key]
            current_clip['ind0'] = min(current_clip['ind0'], next_clip['ind0'])
            current_clip['ind1'] = max(current_clip['ind1'], next_clip['ind1'])
            current_clip['alert_label'] = max(current_clip['alert_label'], next_clip['alert_label'])
            del (data[i])

        if current_clip["file1"] == next_clip["file0"] and current_clip["ind1"] > next_clip["ind0"]:
            for key in ['ids', 'Classes', 'Alert Types', 'scores']:
                current_clip[key] = current_clip[key] + next_clip[key]
            current_clip['ind1'] = next_clip['ind1']
            current_clip["file1"] = next_clip["file1"]
            current_clip['alert_label'] = max(current_clip['alert_label'], next_clip['alert_label'])

            del (data[i])

    for i, line in enumerate(data):
        input_filename1 = os.path.join(video_path, line["file0"])
        if not os.path.exists(input_filename1):
            print(input_filename1, " not found!")
            continue
        alert_label = get_alert_label(alerts_df, line, df_scores)
        start_frame1 = line["ind0"]
        try:
            video1 = VideoFileClip(input_filename1)
        except:
            continue

        out_filename, indices = get_output_filename(line["Alert Types"], line["Classes"], line["ids"],
                                                    line["scores"], line["NCarsLeft"] + line["NCarsRight"],
                                                    line["file0"], alert_label,
                                                    free_text, out_folder, indices)
        data_log.append({"Filename": out_filename, "Type": line["Alert Types"][0],
                         "Start Frame": line["ind0"], "Start File": line["file0"],
                         "End Frame": line["ind1"], "End File": line["file0"]})
        if line["file0"] == line["file1"]:
            if not alert_label and file_is_unique(line["file0"], data):
                shutil.copy(input_filename1, out_filename)
                continue
            end_frame1 = line["ind1"]
            start_time = start_frame1 / video1.fps
            end_time = end_frame1 / video1.fps
            try:
                cut_video = video1.subclip(start_time, end_time)

                cut_video.write_videofile(out_filename)
                cut_video.close()
            except:
                pass
        else:
            input_filename2 = os.path.join(video_path, line["file1"])

            video2 = VideoFileClip(input_filename2)

            start_time1 = line["ind0"] / video1.fps
            end_time1 = video1.duration

            start_time2 = 0
            end_time2 = line["ind1"] / video2.fps

            try:
                cut_video1 = video1.subclip(start_time1, end_time1)
                cut_video2 = video2.subclip(start_time2, end_time2)

                final_video = concatenate_videoclips([cut_video1, cut_video2])
                final_video.write_videofile(out_filename)

                final_video.close()
            except:
                continue
    close_all_videos()
    out_df = pd.json_normalize(data_log)
    out_df.to_csv("LogBack.csv")
