import glob
import pandas as pd

csv_paths = glob.glob("data/processed/motogp_*_clean.csv")

dataframe_list = []

for csv in csv_paths:
    dataframe = pd.read_csv(csv)
    dataframe_list.append(dataframe)

dataset = pd.concat(dataframe_list, ignore_index=True)

print("Dataset ready for machine learning, go to machine learning window and test it")
print("Dataset lenght: ", dataset.lenght)