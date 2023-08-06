# Version: 2.0
# Purpose: Scrape AWS info. Used to be divy-legacy/src/master/aws/utils.py
# Company: iSystematics LLC.
# Last updated: 08/31/2022
# By: Steven Crickman
import traceback
import itertools
import json
import logging
import time
import os
import subprocess

log = logging.getLogger(__name__)

def prereq():
    """
    Setup prereqisites for run function
    """
    try:
        subprocess.run("apt-get -o DPkg::Lock::Timeout=-1 update -y", shell=True)
        subprocess.run("apt-get -o DPkg::Lock::Timeout=-1 install postgresql postgresql-contrib python3-pip -y",
                       shell=True)
        subprocess.run("curl -SL https://s3.amazonaws.com/scripts.accuknox.com/steampipe.sh -o /tmp/install.sh", shell=True)
        subprocess.run("bash /tmp/install.sh", shell=True)
        subprocess.run('adduser --disabled-login --gecos "" steampipeuser', shell=True)
        subprocess.run('su - steampipeuser -m -c "steampipe plugin install aws@0.97.0"', shell=True)
        __salt__["pip.install"]("sentry-sdk")
        __salt__["pip.install"]("redis==3.5.3")
        __salt__["pip.install"]("awscli==1.18.207")
        return ""
    except:
        error = traceback.format_exc()
        return error


class SaltWrapper(object):

    def __init__(self):
        self.salt = __salt__
        self.pillar = __pillar__


def _get_data(table):
    """
        The function run steampipeuser command to receive the data
    """
    if table == "aws_kms_key":
        process = subprocess.run(
            "timeout 10m su - steampipeuser -m -c \"steampipe query 'select _ctx, account_id, akas, aliases, arn, aws_account_id, creation_date, customer_master_key_spec, deletion_date, description, enabled, id, key_manager, key_rotation_enabled, key_state, key_usage, origin, partition, policy, policy_std, region, title, valid_to from {}' --output json\"".format(table), shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process = subprocess.run(
            "timeout 10m su - steampipeuser -m -c \"steampipe query 'select * from {}' --output json\"".format(table), shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not process.returncode == 0:
        error = "Failed to run query on table {}. {}".format(table, process.stderr.decode('utf-8', 'ignore'))
        log.error(error)
        _check_sentry()
        return False, error
    if not process.stdout and process.stderr:
        error = "Failed to run query on table {}. {}".format(table, process.stderr.decode('utf-8', 'ignore'))
        log.error(error)
        _check_sentry()
        return False, error
    if not process.stdout:
        return False, "The process was killed when attempting to query table {}.".format(table)
    return True, process.stdout.decode('utf-8', 'ignore')


def run(source_key_id=None, source_key=None, source_key_token=None, regions=None, label=None, redis_write_key=None,
        redis_tls_host=None, redis_tls_port=None, redis_tls_password=None):
    """
    This function scrapes AS information and uploads it to S3
        source_key_id: ''                          # aws key id for the account to use to scrape aws information
        source_key: ''                             # aws key for the account to use to scrape aws information
        source_key_token: ''                        # Optional parameter if using STS assume role.
        regions : 'us-east-1, us-east-2'           # You can enter one region or multiple. If entering multiple regions
                                                   # It must be a comma separated list
                                                   # example: us-east-1, us-east-2, us-west-2
        label: 'TEST'                              # label to attach to filename
        redis_write_key
        redis_tls_host
        redis_tls_port
        redis_tls_password
    """
    errorMessage = prereq()
    if errorMessage:
        return errorMessage

    global_table_list = ["aws_account", "aws_iam_user", "aws_iam_role", "aws_iam_group", "aws_iam_policy_attachment", "aws_region"]
    regional_table_list = ["aws_accessanalyzer_analyzer", "aws_cloudtrail_trail", "aws_cloudwatch_metric", "aws_ebs_volume", "aws_ebs_snapshot", "aws_ec2_instance", "aws_ec2_network_interface", "aws_ec2_network_load_balancer", "aws_kms_key", "aws_ecs_cluster", "aws_eks_cluster", "aws_elasticache_cluster", "aws_lambda_function", "aws_rds_db_instance", "aws_rds_db_cluster", "aws_s3_bucket", "aws_vpc", "aws_vpc_subnet", "aws_vpc_eip", "aws_vpc_nat_gateway", "aws_vpc_security_group", "aws_vpc_security_group_rule", "aws_vpc_network_acl", "aws_vpc_route", "aws_vpc_peering_connection", "aws_workspaces_workspace"]
    data = {}
    os.environ['AWS_ACCESS_KEY_ID'] = source_key_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = source_key
    if source_key_token: os.environ["AWS_SESSION_TOKEN"] = source_key_token

    for table in global_table_list:
        success, output = _get_data(table)
        if not success:
            return output
        else:
            data.update({table: json.loads(output)})

    success, output = _get_data("aws_iam_policy where is_attached")

    if not success:
        return output
    else:
        data.update({"attached_aws_iam_policy": json.loads(output)})

    for table in regional_table_list:
        data_dict = {}
        for region in regions:
            os.environ['AWS_DEFAULT_REGION'] = region
            success, output = _get_data(table)
            if not success:
                return output
            else:
                data_dict.update({region: json.loads(output)})
        data.update({table: data_dict})

    # Save to file

    filename = os.path.join("/tmp", "{}-AM-{}.json".format(label, time.time()))

    with open(filename, 'w') as f:
        f.write(json.dumps(data, default=str))

    r.sadd(redis_write_key, filename)

    return "Success! File written to {}".format(filename)
