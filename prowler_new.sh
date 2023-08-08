#!/bin/bash

. .awsconfig

[[ ! -f "./prowler/prowler" ]] && echo "local prowler repo not found" && exit 2

cd prowler
[[ $? -ne 0 ]] && echo "prereq installation failed" && exit 3

pdir=$DATADIR/prowler
mkdir -p $pdir

LOG=$DATADIR/prowler.log
#for region in ${regions[@]}; do
	SECONDS=0
	outfile=$DATADIR/prowler_${region}.json
#    echo "./index.js --json=$outfile --console=none $compliance $suppstr"
	echo "executing for region=$region ... starting at $SECONDS"
    ./prowler -M json -o $pdir >$LOG 2>$LOG
	((total+=$SECONDS))
	echo "Region=$region, Time=${SECONDS}s, Total=${total}s"
#done
