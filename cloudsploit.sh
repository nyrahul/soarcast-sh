#!/bin/bash

. .awsconfig

suppressed_regions=("us-east-1" "us-east-2" "us-west-1" "us-west-2" "af-south-1" "ap-east-1"
                    "ap-southeast-3" "ap-south-1" "ap-northeast-3" "ap-northeast-2" "ap-southeast-1"
                    "ap-southeast-2" "ap-northeast-1" "ca-central-1" "eu-central-1" "eu-west-1"
                    "eu-west-2" "eu-south-1" "eu-west-3" "eu-north-1" "me-south-1" "me-central-1"
                    "sa-east-1")

[[ ! -d "./cloudsploit/plugins/aws/" ]] && echo "local cloudsploit repo not found" && exit 2

cd cloudsploit && npm install 2>/dev/null && chmod +x index.js
[[ $? -ne 0 ]] && echo "prereq installation failed" && exit 3

compliance="--compliance=hipaa --compliance=pci --compliance=cis --compliance=cis1 --compliance=cis2"

function get_suppressed_regions()
{
	suppreg=("${suppressed_regions[@]}")
	for reg in $1; do
		suppreg=("${suppreg[@]/$reg}")
	done
	suppstr=""
	for reg in ${suppreg[@]}; do
		suppstr+="--suppress *:$reg:* " 
	done
	
}

for region in ${regions[@]}; do
	SECONDS=0
	export AWS_REGION="$region"
	get_suppressed_regions "$region"
	outfile=$DATADIR/cloudsploit_${region}.json
#    echo "./index.js --json=$outfile --console=none $compliance $suppstr"
    bash ./index.js --json=$outfile --console=none $compliance $suppstr 2>/dev/null >/dev/null
	((total+=$SECONDS))
	echo "Region=$region, Time=${SECONDS}s. Total=${total}s"
done
