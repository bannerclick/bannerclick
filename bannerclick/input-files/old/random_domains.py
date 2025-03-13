import pprint
import csv
import os
import random


curr_script_dir = os.path.dirname(os.path.realpath(__file__))


def find_domain_rank(csv_filename):
    domain_rank_map = {}
    with open(os.path.join(curr_script_dir, csv_filename), newline='') as csvfile:
        reader = csv.reader(csvfile)
        for rank, row in enumerate(reader):
            if rank > 101_000:
                break
            rank, domain = row
            if not rank.isdigit():
                continue
            domain_rank_map[domain] = int(rank)
    return domain_rank_map


domain_ranks = find_domain_rank(r'top-1m.csv')
filtered_domains = [
    (domain, rank) for domain, rank
    in domain_ranks.items()
    if rank <= 50_000
]

sampled_domain_rank_pairs = random.sample(filtered_domains, 20_000)

with open(os.path.join(curr_script_dir, r'50k_random.csv'), 'w', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(['', 'domain', 'rank'])
    for idx, (domain, rank) in enumerate(sampled_domain_rank_pairs):
        writer.writerow([idx, domain, rank])
