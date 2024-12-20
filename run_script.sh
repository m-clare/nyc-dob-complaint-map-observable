#!/usr/bin/env sh

cd ~/workspaces/nyc-dob-observable/
direnv allow
rm ./src/.observablehq/cache/complaints.csv

npm run build
scp -r ./dist/* "$SERVER:$SERVER_DIR"
