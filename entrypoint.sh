#!/usr/bin/env bash

usage()
{
cat << EOF
usage: $0 options

OPTIONS:
    -e  AWS credential key, e.g dev.json
    -m  VPC main ID
    -i  AMI ID
    -n  New VPC name
    -c  New VPC CIDR
    -s  New VPC SUBNET

EOF
}

while getopts "e:m:i:n:c:s:" OPTION;do
    case $OPTION in
        u)
            usage
            exit 1
            ;;
        e)
            ENV=$OPTARG
            ;;
        m)
            MAINID=$OPTARG
            ;;
        i)
            AMIID=$OPTARG
            ;;
        n)
            VPCNAME=$OPTARG
            ;;
        c)
            VPCCIDR=$OPTARG
            ;;
        s)
            VPCSUBNET=$OPTARG
            ;;
        ?)
            usage
            exit
            ;;
    esac
done

echo "Entering to vpc-creation script..."

python vpc-create.py --env "$ENV.json" --main-id $MAINID --ami-id $AMIID --vpc-name $VPCNAME --vpc-cidr $VPCCIDR --vpc-subnet $VPCSUBNET
