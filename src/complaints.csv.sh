#!/usr/bin/env sh

DATE=$(date +%Y-%m-%d)

cd ~/workspaces/nyc-dob-observable/src/data || exit
~/.virtualenvs/nyc-dob/bin/python3 complaints.py

tippecanoe -z20 -o "nyc-buildings.pmtiles" -r1 '--cluster-distance=1' --cluster-densest-as-needed --no-tile-size-limit --extend-zooms-if-still-dropping "${DATE}_nycdob_rollup.json" -l "nyc-buildings" --force

rm "${DATE}_nycdob_rollup.json"
