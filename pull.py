# Author: Loran Knol
"""
Script to pull all of Alex's BiAffect data.

This script uses the `synapse get` shell command that comes with the Python
installation. (Unfortunately, the analogous Python function synapseclient.get
does not seem to have quite the same functionality.)

Assumes you have a ~/.synapseConfig file that allows you to run the synapse
command without further authentication (see
https://python-docs.synapse.org/tutorials/authentication/#use-synapseconfig).

The download_dir variable should be replaced by a path specific
to your system.
"""

import subprocess
import os
from os.path import join
import synapseclient
from dotenv import load_dotenv

load_dotenv()

syn = synapseclient.Synapse()
#syn.login(silent=True)
syn.login(authToken=os.environ.get('SYNAPSE_AUTH_TOKEN')) 

# Replace with path suitable to your system
download_dir = "add path" # TMPDIR is specific to the Donders HPC

#  Health codes
health_codes = [
    "add your own health code"
]

# Tabular overview of all files in 'Test Study Project ucMft' in Synapse
view_id = 'syn64728532'

# ('health_code[0]', 'health_code[1]', ...)
hc_clause = "('" + "', '".join(health_codes) + "')"

query_str = f"SELECT * FROM {view_id} WHERE healthCode IN {hc_clause}"

# Set capture_output to True to collect output in sp.stdout and sp.stderr
sp = subprocess.run([
    'synapse', 'get',
    '-q', query_str,
    '--downloadLocation', download_dir,
    '--multiThreaded'
], capture_output=False)

# 0 in case of success
message = 'Success' if sp.returncode == 0 else 'Error'
print(message)

# Execute the query again to retrieve the associated health codes
meta = syn.tableQuery(query_str, downloadLocation=download_dir) \
    .asDataFrame()
# For quick indexing by file name during parsing
meta = meta.set_index('name')

hc_series = meta['healthCode']

hc_series.to_frame().to_parquet(join(download_dir, 'hc_df.parquet'))
