import subprocess
import time
import signal,psutil
p = subprocess.Popen(
            "timeout 1 steampipe query 'select _ctx, account_id, akas, aliases, arn, aws_account_id, creation_date, customer_master_key_spec, deletion_date, description, enabled, id, key_manager, key_rotation_enabled, key_state, key_usage, origin, partition, policy, policy_std, region, title, valid_to from aws_kms_key' --output json", shell=True)

for child in psutil.Process(p.pid).get_children(recursive=True):
    child.send_signal(signal.SIGINT)

print("sleeping")
time.sleep(30)
