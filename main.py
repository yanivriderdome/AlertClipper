import pandas as pd
from BlindSpotClipper import BlindSpotClipper

camera = "Back"
filename = r"J:\BackAlerts.csv"
if camera == "Front":
    filename = r"J:\FrontAlerts.csv"

video_path = r"J:\Videos"
free_text = "Motherson"

vehicles = {-1: "Unknown", 0: "Car", 1: "Bus", 2: "Truck", 3: "Bike"}
names_dict = {"Right BlindSpot": {3: "Bike_Blind_Spot_Right_", 0: "Right_Blind_Spot_"},
              "Left BlindSpot": {3: "Bike_Blind_Spot_Left_", 0: "Left_Blind_Spot_"},
              "Both BlindSpots": {3: "Bike_Blind_Spot_Left_And_Right_", 0: "Blind_Spots_"},
              "Front_Distance": {3: "Front_Distance_Bike", 0: "Blind_Spots_"}}

indices_filename = "indices.csv"
indices_df = pd.read_csv(indices_filename)
Out_folder = "Videos"

inds_falses = {}

BlindSpotClipper(indices_filename, filename, indices_df, Out_folder, free_text, video_path)