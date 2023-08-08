#!/bin/bash

. .awsconfig

#regions=("ap-south-1" "eu-north-1" "eu-west-3" "eu-west-2" "eu-west-1" "ap-northeast-3" "ap-northeast-2" "ap-northeast-1" "ca-central-1" "sa-east-1" "ap-southeast-1" "ap-southeast-2" "eu-central-1" "us-east-1" "us-east-2" "us-west-1" "us-west-2")

global_table_list=("aws_account" "aws_iam_user" "aws_iam_role" "aws_iam_group" "aws_iam_policy_attachment" "aws_region")
regional_table_list=("aws_accessanalyzer_analyzer" "aws_cloudtrail_trail" "aws_cloudwatch_metric" "aws_ebs_volume" "aws_ebs_snapshot" "aws_ec2_instance" "aws_ec2_network_interface" "aws_ec2_network_load_balancer" "aws_kms_key" "aws_ecs_cluster" "aws_eks_cluster" "aws_elasticache_cluster" "aws_lambda_function" "aws_rds_db_instance" "aws_rds_db_cluster" "aws_s3_bucket" "aws_vpc" "aws_vpc_subnet" "aws_vpc_eip" "aws_vpc_nat_gateway" "aws_vpc_security_group" "aws_vpc_security_group_rule" "aws_vpc_network_acl" "aws_vpc_route" "aws_vpc_peering_connection" "aws_workspaces_workspace")

function get_data()
{
	if [ "$table" == "aws_kms_key" ]; then
		steampipe query 'select _ctx, account_id, akas, aliases, arn, aws_account_id, creation_date, customer_master_key_spec, deletion_date, description, enabled, id, key_manager, key_rotation_enabled, key_state, key_usage, origin, partition, policy, policy_std, region, title, valid_to from aws_kms_key' --output json
	else
		steampipe query "select * from $table;" --output json
	fi
}

total=0
for region in ${regions[@]}; do
	regtotal=0
	unset AWS_DEFAULT_REGION
	for table in ${global_table_list[@]}; do
		SECONDS=0
		get_data >$DATADIR/${table}__${region}.json
		((total+=$SECONDS))
		((regtotal+=$SECONDS))
		echo "Region=$region, Table=$table, Time=${SECONDS}s. RegionTotal=${regtotal}s, Total=${total}s"
	done

	echo "aws_iam_policy"
	steampipe query 'select * from aws_iam_policy where is_attached' --output json >"$DATADIR/aws_iam_policy__${region}.json"
	exit

	export AWS_DEFAULT_REGION=$region
	for table in ${regional_table_list[@]}; do
		SECONDS=0
		get_data >tee $DATADIR/${table}__${region}.json
		((total+=$SECONDS))
		((regtotal+=$SECONDS))
		echo "Region=$region, Table=$table, Time=${SECONDS}s. RegionTotal=${regtotal}s, Total=${total}s"
	done
	wait
	echo "----------- $region region took ${regtotal}s to scan ------------"
done
