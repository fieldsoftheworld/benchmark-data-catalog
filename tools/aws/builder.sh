#!/usr/bin/env bash
# Manage the EC2 instance that builds catalog datasets.
#
#   tools/aws/builder.sh launch [branch]   # create key/SG if needed, start one instance
#   tools/aws/builder.sh list              # every builder, with its name and IP
#   tools/aws/builder.sh ssh               # ssh in (forwards 8400 for source-coop login)
#   tools/aws/builder.sh status
#   tools/aws/builder.sh stop | start
#   tools/aws/builder.sh allow-my-ip       # re-open SSH after your IP changes
#   tools/aws/builder.sh terminate         # deletes the instance AND its disk (staging/)
#
# One instance per FTW_BUILDER name, found by its Name tag: ftw-catalog-builder for the
# default builder, ftw-catalog-builder-<FTW_BUILDER> for extra ones (FTW_BUILDER=jp
# tools/aws/builder.sh launch). All builders share one key pair and SSH security group.
# us-west-2 because the Source Cooperative
# bucket, Sentinel-2 COGs and the quarterly mosaics all live there. SSH is the
# only way in (the SSO PowerUser role cannot create the IAM role Session Manager
# needs) and is open to your current IP only. The instance stops itself after
# an hour idle (tools/aws/bootstrap.sh); `stop` keeps the disk, `terminate` doesn't.
#
# Environment: AWS_PROFILE (default tg), FTW_BUILDER (default: the main builder),
# FTW_INSTANCE_TYPE (default r7i.4xlarge), FTW_DISK_GB (default 1000).
set -euo pipefail
# macOS ships bash 3.2, where set -e does not reach inside $(...): every AWS call
# whose output is captured ends in `|| exit 1` so a failure stops the script.

export AWS_PROFILE="${AWS_PROFILE:-tg}"
export AWS_REGION=us-west-2
BASE=ftw-catalog-builder
NAME="$BASE${FTW_BUILDER:+-$FTW_BUILDER}"
KEY_FILE="$HOME/.ssh/$BASE.pem"
INSTANCE_TYPE="${FTW_INSTANCE_TYPE:-r7i.4xlarge}"
DISK_GB="${FTW_DISK_GB:-1000}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AMI_PARAM=/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id

instance_id() {
    aws ec2 describe-instances \
        --filters "Name=tag:Name,Values=$NAME" \
        "Name=instance-state-name,Values=pending,running,stopping,stopped" \
        --query 'Reservations[].Instances[].InstanceId' --output text
}

public_ip() {
    aws ec2 describe-instances --instance-ids "$1" \
        --query 'Reservations[].Instances[].PublicIpAddress' --output text
}

security_group() {
    aws ec2 describe-security-groups --filters "Name=group-name,Values=$BASE-ssh" \
        --query 'SecurityGroups[].GroupId' --output text
}

my_cidr() { echo "$(curl -fsS https://checkip.amazonaws.com)/32"; }

ensure_key() {
    if [[ -f "$KEY_FILE" ]]; then return; fi
    aws ec2 create-key-pair --key-name "$BASE" --key-type ed25519 \
        --query KeyMaterial --output text > "$KEY_FILE"
    chmod 600 "$KEY_FILE"
    echo "created key pair $BASE -> $KEY_FILE"
}

ensure_security_group() {
    local sg
    sg=$(security_group) || exit 1
    if [[ -z "$sg" ]]; then
        local vpc
        vpc=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true \
            --query 'Vpcs[0].VpcId' --output text) || exit 1
        sg=$(aws ec2 create-security-group --group-name "$BASE-ssh" --vpc-id "$vpc" \
            --description "SSH to $BASE builders from the maintainer IP" --query GroupId --output text) \
            || exit 1
        echo "created security group $sg" >&2
    fi
    allow_ip "$sg" >&2 || exit 1
    echo "$sg"
}

allow_ip() {
    local sg="$1" cidr err
    [[ -n "$sg" ]] || { echo "no $BASE-ssh security group" >&2; exit 1; }
    cidr=$(my_cidr)
    if err=$(aws ec2 authorize-security-group-ingress --group-id "$sg" \
        --protocol tcp --port 22 --cidr "$cidr" 2>&1 >/dev/null); then
        echo "opened SSH to $cidr"
    elif [[ "$err" == *InvalidPermission.Duplicate* ]]; then
        echo "SSH already open to $cidr"
    else
        echo "$err" >&2
        exit 1
    fi
}

cmd_launch() {
    local branch="${1:-main}" existing
    existing=$(instance_id)
    if [[ -n "$existing" ]]; then
        echo "$NAME already exists: $existing (use start/ssh)"; exit 1
    fi
    ensure_key
    local sg ami user_data id
    sg=$(ensure_security_group)
    ami=$(aws ssm get-parameter --name "$AMI_PARAM" --query Parameter.Value --output text)
    user_data=$(mktemp)
    { echo '#!/usr/bin/env bash'; echo "export FTW_CATALOG_BRANCH=$branch";
      tail -n +2 "$HERE/bootstrap.sh"; } > "$user_data"
    id=$(aws ec2 run-instances --image-id "$ami" --instance-type "$INSTANCE_TYPE" \
        --key-name "$BASE" --security-group-ids "$sg" \
        --instance-initiated-shutdown-behavior stop \
        --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=$DISK_GB,VolumeType=gp3,Throughput=500,Iops=6000,DeleteOnTermination=true}" \
        --metadata-options HttpTokens=required \
        --user-data "file://$user_data" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME},{Key=Project,Value=ftw}]" \
            "ResourceType=volume,Tags=[{Key=Name,Value=$NAME},{Key=Project,Value=ftw}]" \
        --query 'Instances[0].InstanceId' --output text)
    rm -f "$user_data"
    echo "launched $id ($INSTANCE_TYPE, ${DISK_GB} GB, branch $branch); waiting for it to run..."
    aws ec2 wait instance-running --instance-ids "$id"
    echo "running at $(public_ip "$id"). Bootstrap takes ~10 min; then: tools/aws/builder.sh ssh"
}

cmd_ssh() {
    local id ip
    id=$(instance_id); [[ -n "$id" ]] || { echo "no $NAME instance"; exit 1; }
    ip=$(public_ip "$id"); [[ "$ip" != "None" && -n "$ip" ]] || { echo "$id is not running"; exit 1; }
    exec ssh -i "$KEY_FILE" -o StrictHostKeyChecking=accept-new \
        -L 8400:127.0.0.1:8400 "ubuntu@$ip" "$@"
}

cmd_status() {
    aws ec2 describe-instances --filters "Name=tag:Name,Values=$NAME" \
        --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name,PublicIpAddress,LaunchTime]' \
        --output table
}

cmd_list() {
    aws ec2 describe-instances --filters "Name=tag:Name,Values=$BASE,$BASE-*" \
        "Name=instance-state-name,Values=pending,running,stopping,stopped" \
        --query 'Reservations[].Instances[].[Tags[?Key==`Name`]|[0].Value,InstanceId,InstanceType,State.Name,PublicIpAddress,LaunchTime]' \
        --output table
}

cmd_terminate() {
    local id
    id=$(instance_id); [[ -n "$id" ]] || { echo "no $NAME instance"; exit 1; }
    read -r -p "Terminate $id and DELETE its disk (staging/ is lost)? type 'terminate': " answer
    [[ "$answer" == terminate ]] || { echo "aborted"; exit 1; }
    aws ec2 terminate-instances --instance-ids "$id" --output text >/dev/null
    echo "terminating $id"
}

case "${1:-}" in
    launch) shift; cmd_launch "$@" ;;
    ssh) shift; cmd_ssh "$@" ;;
    status) cmd_status ;;
    list) cmd_list ;;
    stop) aws ec2 stop-instances --instance-ids "$(instance_id)" --output text >/dev/null && echo stopping ;;
    start) aws ec2 start-instances --instance-ids "$(instance_id)" --output text >/dev/null \
        && aws ec2 wait instance-running --instance-ids "$(instance_id)" && cmd_status ;;
    allow-my-ip) allow_ip "$(security_group)" ;;
    terminate) cmd_terminate ;;
    *) sed -n '2,22p' "$0"; exit 1 ;;
esac
