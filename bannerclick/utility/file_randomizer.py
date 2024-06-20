import pandas as pd

FILE_NAME = r"2k-Tranco5Nov.csv"

FILE_NAME = r"top-1m.csv"
INPUT_FILE_DIR_PATH = r'../input-files/'
INPUT_FILE = INPUT_FILE_DIR_PATH + FILE_NAME

OUTPUT_FILE_NAME = r'20k-' + 'top-1m' + r'-randomized.csv'
OUTPUT_FILE = INPUT_FILE_DIR_PATH + OUTPUT_FILE_NAME

df = pd.read_csv(INPUT_FILE)
df = df[['domain']]
headers = [''] + list(df.columns.values)
df = df.sample(frac=1).reset_index(drop=True)
df.insert(0, '', range(1, len(df) + 1))
df.to_csv(OUTPUT_FILE, index=False, header=headers)
