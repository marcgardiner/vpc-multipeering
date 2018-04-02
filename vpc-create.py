import sys
import argparse
import json

import boto3
from botocore.exceptions import ClientError


#****************   AWS Credential  ***********
AWS_ACCOUNT_ID = ''
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
REGION_NAME = ''
#**********************************************

VPC_MAIN_ID = ''

AMI_ID = ''
VPC_NAME = ''
VPC_CIDR = ''
VPC_SUBNET = ''


def main():
    global AWS_ACCOUNT_ID, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, REGION_NAME
    global VPC_MAIN_ID, AMI_ID, VPC_NAME, VPC_CIDR, VPC_SUBNET

    parser = argparse.ArgumentParser(description="vpc creation")
    parser.add_argument('-e', '--env', help="The configuration file. i.e dev.json", required=True)
    parser.add_argument('-m', '--main-id', help="The main VPC ID", required=True)
    parser.add_argument('-a', '--ami-id', help="The AWS AMI ID", required=True)
    parser.add_argument('-n', '--vpc-name', help="The New VPC name", required=True)
    parser.add_argument('-c', '--vpc-cidr', help="The New VPC CIDR", required=True)
    parser.add_argument('-s', '--vpc-subnet', help="The New VPC SUBNET", required=True)

    args = vars(parser.parse_args())
    config_data_file = args['env']

    VPC_MAIN_ID = args['main_id']
    AMI_ID = args['ami_id']
    VPC_NAME = args['vpc_name']
    VPC_CIDR = args['vpc_cidr']
    VPC_SUBNET = args['vpc_subnet']

    if config_data_file == '':
        print("Please specify environment file")
        sys.exit()
    if AMI_ID == '':
        print("Please input AMI ID")
        sys.exit()
    if VPC_MAIN_ID == '':
        print("Please input MAIN ID")
        sys.exit()
    if VPC_NAME == '':
        print("Please input New VPC Name")
        sys.exit()
    if VPC_CIDR == '':
        print("Please input New VPC CIDR")
        sys.exit()
    if VPC_SUBNET == '':
        print("Please input New VPC SUBNET")
        sys.exit()

    try:
        with open(config_data_file) as data_file:
            data = json.load(data_file)

            for key, value in data["credential"].items():
                if key == "AWS_ACCOUNT_ID":
                    AWS_ACCOUNT_ID = value
                if key == "AWS_ACCESS_KEY_ID":
                    AWS_ACCESS_KEY_ID = value
                if key == "AWS_SECRET_ACCESS_KEY":
                    AWS_SECRET_ACCESS_KEY = value
                if key == "REGION_NAME":
                    REGION_NAME = value

    except Exception as ex:
        print(ex)
        sys.exit(1)

    conn = boto3.resource('ec2', aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                          region_name=REGION_NAME)
    create_vpc(conn)


def create_vpc(conn):
    conn = boto3.resource('ec2', aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                          region_name=REGION_NAME)
    print("Connection established")

    vpc = conn.create_vpc(CidrBlock=VPC_CIDR)
    vpc.create_tags(Tags=[{"Key": "Name", "Value": VPC_NAME}])
    vpc.wait_until_available()
    print("VPC Created")

    gateway = conn.create_internet_gateway()
    vpc.attach_internet_gateway(InternetGatewayId=gateway.id)
    print(gateway.id)

    route_table = conn.create_route_table(VpcId=vpc.id)
    print(route_table.id)

    subnet = conn.create_subnet(CidrBlock=VPC_CIDR, VpcId=vpc.id)
    print(subnet.id)

    route_table.associate_with_subnet(SubnetId=subnet.id)
    print("associated with routing table")

    sg = conn.create_security_group(GroupName=VPC_NAME,
                                    Description=VPC_NAME,
                                    VpcId=vpc.id)
    sg.authorize_ingress(IpProtocol='icmp', FromPort=-1, ToPort=-1, CidrIp='0.0.0.0/0')
    print(sg.id)

    instances = conn.create_instances(
        ImageId=AMI_ID, InstanceType='t2.micro', MaxCount=1, MinCount=1,
        NetworkInterfaces=[{'SubnetId': subnet.id,
                            'DeviceIndex': 0,
                            'AssociatePublicIpAddress': True,
                            'Groups': [sg.group_id]}])
    instances[0].wait_until_running()

    print(instances[0].id)

    create_vpc_peering_connection(vpc.id)


def create_vpc_peering_connection(requester_vpc_id):
    ec2_c = boto3.client('ec2', aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                         region_name=REGION_NAME)

    peer_connection = ec2_c.create_vpc_peering_connection(
        DryRun=False,
        PeerOwnerId=AWS_ACCOUNT_ID,
        PeerVpcId=VPC_MAIN_ID,
        VpcId=requester_vpc_id,
        PeerRegion=REGION_NAME
    )
    peer_conn_id = peer_connection['VpcPeeringConnection']['VpcPeeringConnectionId']

    print(peer_conn_id)

    res_acceptance = ec2_c.accept_vpc_peering_connection(DryRun=False, VpcPeeringConnectionId=peer_conn_id)
    configure_peer_route(ec2_c, peer_conn_id, VPC_MAIN_ID, requester_vpc_id)


def configure_peer_route(ec2_c, peer_conn_id, requester_vpc_id, accepter_vpc_id):
    cnxn = ec2_c.describe_vpc_peering_connections(VpcPeeringConnectionIds=[peer_conn_id])

    print(cnxn)

    update_route_tables(peer_conn_id, requester_vpc_id ,accepter_vpc_id)
    update_route_tables(peer_conn_id, accepter_vpc_id, requester_vpc_id)

    print("Done!")


def update_route_tables(ec2_c, peer_conn_id, src_vpc_id, dest_vpc_id):
    route_dests = []
    route_dests = find_route_destinations(ec2_c, src_vpc_id)

    route_tables = ec2_c.describe_route_tables()

    for rt in route_tables['RouteTables']:
        if rt['VpcId'] == dest_vpc_id:
            add_routes(rt, route_dests, peer_conn_id)


def add_routes(rt, route_dests, peer_conn_id):
    rt_id = rt['RouteTableId']
    ec2_r = boto3.resource('ec2', aws_access_key_id=AWS_ACCESS_KEY_ID,
                   aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                   region_name=REGION_NAME)
    route_table = ec2_r.RouteTable(rt_id)

    print(route_table)

    for r in route_dests:
        try:
            if ":" in r:
                route_table.create_route(
                    DestinationIpv6CidrBlock=r,
                    VpcPeeringConnectionId=peer_conn_id,
                    RouteTableId=rt_id
                )
            else:
                route_table.create_route(
                    DestinationCidrBlock=r,
                    VpcPeeringConnectionId=peer_conn_id,
                    RouteTableId=rt_id
                )

            print("Added route to {0} in table {1}.").format(r, rt_id)

        except ClientError as e:
            if e.response['Error']['Code'] == 'RouteAlreadyExists':
                print("Route already exists for {0} in table {1}").format(r, rt_id)
            else:
                print(e)
                sys.exit(1)


def find_route_destinations(ec2_c, vpc_id):
    dest_cidrs = []
    dest_vpc = ec2_c.describe_vpcs(VpcIds=[vpc_id])
    dest_vpc = dest_vpc['Vpcs'][0]
    dest_cidrs.append(dest_vpc['CidrBlock'])

    if 'Ipv6CidrBlockAssociationSet' in dest_vpc.keys():
        dest_cidrs.append(dest_vpc['Ipv6CidrBlockAssociationSet'][0]['Ipv6CidrBlock'])

    return dest_cidrs


if __name__ == "__main__":
    main()
