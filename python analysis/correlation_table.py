#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 15:57:08 2025

@author: dtopping
"""


import pandas as pd
import numpy as np
from scipy.stats import pearsonr
import seaborn as sns
import matplotlib.pyplot as plt


infile = '/t1/topping/point_data/single_value_metrics.csv'
df = pd.read_csv(infile)
df.drop('hydro_mass_bad',axis=1,inplace=True)

corr_matrix = df.corr(method='pearson',numeric_only=True)
# print(corr_matrix)

mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)

plt.figure(figsize=(25, 20))
sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm', linewidths=0.5)
plt.show()


# Extract the lower triangle correlations
lower_triangle_correlations = abs(corr_matrix.mask(mask)).stack().reset_index()
lower_triangle_correlations.columns = ['Variable1', 'Variable2', 'Correlation']

thirds = np.percentile(lower_triangle_correlations['Correlation'], 
                       [33.33, 66.67])

# Plot the histogram of the correlations
# plt.figure(figsize=(10, 6))
# sns.histplot(lower_triangle_correlations['Correlation'], bins=40, kde=True)
# plt.title('Histogram of Correlations (Lower Triangle)')
# plt.xlabel('Correlation')
# plt.ylabel('Frequency')
# plt.show()

df_dropped = df.drop(columns=['simulation','regime'])

threshold = thirds[1]
high_corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr_value = corr_matrix.iloc[i,j]
        
        if abs(corr_value) > threshold:
            # Calculate p-value for statistical significance
            pearson_stat,p_value = pearsonr(df_dropped.iloc[:,i], 
                                            df_dropped.iloc[:,j])
            
            if p_value < 0.05:  # Assuming a significance level of 0.05
                high_corr_pairs.append((corr_matrix.index[i],
                                        corr_matrix.columns[j],
                                        corr_value))



