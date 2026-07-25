"""Reproduces the §4.3 leaderboard confidence-interval and significance analysis."""
import numpy as np
from scipy import stats
from math import ceil
N=120
def wilson(p,n=N,z=1.96):
    d=1+z*z/n;c=p+z*z/(2*n);h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n));return (c-h)/d,(c+h)/d
def twoprop(p1,p2,n=N):
    pp=(p1+p2)/2;se=np.sqrt(2*pp*(1-pp)/n);z=(p1-p2)/se;return z,2*(1-stats.norm.cdf(abs(z)))
def n_for_gap(p1,p2,a=0.05,pw=0.8):
    za=stats.norm.ppf(1-a/2);zb=stats.norm.ppf(pw);pp=(p1+p2)/2
    return ceil((za*np.sqrt(2*pp*(1-pp))+zb*np.sqrt(p1*(1-p1)+p2*(1-p2)))**2/(p1-p2)**2)
sysd=[('Poetiq (SOTA)',.54),('Gemini3 Pro +refine',.54),('Gemini3 Deep Think',.45),('Opus 4.5 Thinking',.376),('Kaggle25 winner',.2403)]
for n,p in sysd:
    lo,hi=wilson(p);print(f'{n:24s} {p*100:5.1f}%  CI[{lo*100:.1f},{hi*100:.1f}]')
z,pv=twoprop(.54,.45);print(f'\n54 vs 45: z={z:.2f} p={pv:.3f}')
print('tasks for 5pt gap @80% power:',n_for_gap(.50,.45))
