import glob
import pandas as pd

csv_paths = glob.glob("data/processed/*.csv")

dataframe_list = []

for csv in csv_paths:
    dataframe = pd.read_csv(csv)
    dataframe_list.append(dataframe)

dataset = pd.concat(dataframe_list, ignore_index=True)

print(dataset)