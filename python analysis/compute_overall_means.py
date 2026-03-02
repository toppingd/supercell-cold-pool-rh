import pandas as pd
from pathlib import Path

def process_means(csv, valname):
    df = pd.read_csv(csv, header=None)
    df.columns = ['simulation'] + [f'time_{i}' for i in range(1, df.shape[1])]
    # Compute mean across timesteps
    df[valname] = df.loc[:, df.columns[1:]].mean(axis=1)
    return df[['simulation', valname]]

inpath = Path('/storm/topping/cold_pools/sim_means')

means_dfs = {
    'b': process_means(inpath / 'buoyancy_means.csv', 'b'),
    'area': process_means(inpath / 'areas.csv', 'area'),
    'depth': process_means(inpath / 'depth_means.csv', 'depth'),
    'prate': process_means(inpath / 'prate_means.csv', 'prate'),
    'lh_norm': process_means(inpath / 'lh_norm_means_500m.csv', 'lh_norm'),
}

# Merge all means on simulation name
df = means_dfs['b']
for key in ['area', 'depth', 'prate', 'lh_norm']:
    df = df.merge(means_dfs[key], on='simulation')

df[['simulation_base', 'regime']] = df['simulation'].str.rsplit('-', n=1, expand=True)
df = df[['simulation_base', 'regime', 'b', 'area', 'depth', 'prate', 'lh_norm']]

# Compute group means (overall for each simulation_base)
overall = df.groupby('simulation_base')[['b', 'area', 'depth', 'prate', 'lh_norm']].mean().reset_index()
overall['regime'] = 'overall'
overall = overall[['simulation_base', 'regime', 'b', 'area', 'depth', 'prate', 'lh_norm']]
# Concatenate original and overall rows
final_df = pd.concat([df, overall], ignore_index=True)

final_df = final_df.rename(columns={'simulation_base': 'simulation'})

final_df.to_csv(inpath/'single_value_metrics_FINAL.csv', index=False)