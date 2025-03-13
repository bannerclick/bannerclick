import pandas as pd
import random

TP = 262
FP = 1    # click on No, adjust
TN = 90
FN = 4    # slider uncommon design,  lang, or Selenium fails to click on the detected elements


acc = (TP+TN)/(TP+TN+FP+FN)
print(acc)


exit(1)


# Load the CSV file
file_path = 'top-1m.csv'
df = pd.read_csv(file_path, header=None, names=['Rank', 'Domain'])

# Filter the top 10,000 domains
top_10k = df.head(20000)
sample_state = 42
# Randomly select 1,000 domains
sample_1k = top_10k.sample(n=1000, random_state=sample_state)

# Reset index for the sample
sample_1k = sample_1k.reset_index(drop=True)

# Create new DataFrame with the format you need
formatted_sample_1k = pd.DataFrame({
    '': range(len(sample_1k)),  # Adding a new index column starting from 0
    'domain': sample_1k['Domain'],
    'rank': sample_1k['Rank']
})

# Save the new formatted CSV file
formatted_sample_1k.to_csv('sampled_1k_20k.csv', index=False)

# Optionally, display the formatted DataFrame
print(formatted_sample_1k)
