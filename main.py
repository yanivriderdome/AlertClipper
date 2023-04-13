import pandas as pd
from BlindSpotClipper import BlindSpotClipper
from FrontAlertsClipper import FrontAlertsClipper


camera = "Front"
filename = r"J:\BackAlerts.csv"
if camera == "Front":
    filename = r"J:\FrontAlerts.csv"

video_path = r"J:\Videos"
free_text = "Jakarta"

indices_filename = "indices.csv"
indices_df = pd.read_csv(indices_filename)
Out_folder = "Videos"

inds_falses = {}
if camera == "Front":
    FrontAlertsClipper(indices_filename, filename, indices_df, Out_folder, free_text, video_path)
else:
    BlindSpotClipper(indices_filename, filename, indices_df, Out_folder, free_text, video_path)