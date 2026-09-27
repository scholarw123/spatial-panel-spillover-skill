"""Recreate demo and run the generic extensions without touching any private data."""
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
demo=root/'examples'/'synthetic_demo'
subprocess.run([sys.executable,str(demo/'generate_demo_data.py')],check=True)
subprocess.run([sys.executable,str(root/'scripts'/'run_spatial_panel.py'),str(demo/'config.json')],check=True)
for name in ('v02_weight_diagnostics.csv','v03_global_bivariate_moran.csv','v03_lisa_Y.csv','v04_identification_guard.txt'):
    assert (demo/'outputs'/name).is_file(), f'Missing {name}'
# Structural regression checks: impacts sum and failed/disconnected models are visible.
import pandas as pd
sensitivity=pd.read_csv(demo/'outputs'/'v02_weight_sensitivity_sdm.csv')
assert len(sensitivity)>=4 and (sensitivity['status']=='ok').any()
valid=sensitivity[sensitivity['status']=='ok']
assert ((valid['direct']+valid['indirect']-valid['total']).abs()<1e-6).all()
thresholds=pd.read_csv(demo/'outputs'/'v04_cumulative_thresholds.csv')
assert 'status' in thresholds.columns and 'diagnostic_only_disconnected' in set(thresholds['status'])
print('PASS: synthetic v0.2-v0.4 end-to-end smoke test')
