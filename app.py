import os
import boto3
from dotenv import load_dotenv
from time import sleep
import boto3
import paramiko

load_dotenv()

AWS_REGION = "ap-southeast-1"

KEY_PAIR_NAME = "tact-ec2-key-pair"

PEM_FILE_DIR = "./pem_files"

PEM_FILE = f"{PEM_FILE_DIR}/{KEY_PAIR_NAME}.pem"

AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]

AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]

VPC_ID = os.environ["VPC_ID"]

ec2_client = boto3.client(
                        "ec2",
                        region_name= AWS_REGION,
                        aws_access_key_id = AWS_ACCESS_KEY_ID,
                        aws_secret_access_key = AWS_SECRET_ACCESS_KEY
                        )

def create_key_pair():

    key_pair = ec2_client.create_key_pair(KeyName = KEY_PAIR_NAME)

    private_key = key_pair["KeyMaterial"]

    with os.fdopen(os.open(PEM_FILE, os.O_WRONLY | os.O_CREAT, 0o400), "w+") as handle:

        handle.write(private_key)

def create_instance(sg_id):

    instances = ec2_client.run_instances(

        ImageId         = "ami-0d058fe428540cd89",
        MinCount        = 1,
        MaxCount        = 1,
        InstanceType    = "t2.micro",
        KeyName         = KEY_PAIR_NAME,
        SecurityGroupIds=[sg_id]

    )

    instance_id = instances["Instances"][0]["InstanceId"]

    while True:

        state = get_instance_state(instance_id)

        if state == 'running':
            
            break

        sleep(4)

    print("Instance Running")

    return instance_id

def get_public_ip(instance_id):

    reservations = ec2_client.describe_instances(InstanceIds=[instance_id]).get("Reservations")

    for reservation in reservations:
        for instance in reservation['Instances']:
            ip_address = instance.get("PublicIpAddress")

    return ip_address

def create_sg():

    securitygroup = ec2_client.create_security_group(
                                                    GroupName='tact-sg',
                                                    Description='tact-sg',
                                                    VpcId = VPC_ID
                                                    )

    security_group_id = securitygroup['GroupId']

    ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            {
            'IpProtocol': 'tcp',
            'FromPort': 4500,
            'ToPort': 4500,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ])

    return security_group_id

def get_instance_state(instance_id):

    Myec2 = ec2_client.describe_instances()

    for pythonins in Myec2['Reservations']:

        for printout in pythonins['Instances']:

            # print(printout['InstanceId'])

            if printout['InstanceId'] == instance_id:

                state = printout['State']['Name']

                print(printout['State']['Name'])

            # print(printout['InstanceType'])

    return state

def startpy():

    sg_id = create_sg()

    create_key_pair()

    instance_id = create_instance(sg_id)

    ip_address = get_public_ip(instance_id)

    setup_stuff(ip_address)

    connection_string = ip_address.replace(".","-")

    ssh_command = f'ssh -i "{PEM_FILE_DIR}/{KEY_PAIR_NAME}.pem" ubuntu@ec2-{connection_string}.{AWS_REGION}.compute.amazonaws.com'

    data = {
        "instance_id"   : instance_id,
        "ip_address"    : ip_address,
        "ssh_command"   : ssh_command
    }

    print(data)

    print("Done")

def setup_stuff(instance_ip):

    key = paramiko.RSAKey.from_private_key_file(PEM_FILE)

    client = paramiko.SSHClient()

    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:

        client.connect(hostname=instance_ip, username="ubuntu", pkey=key)

        with open('setup.sh', 'w') as setup:

            script = setup.readlines()

        for cmd in script:

            stdin, stdout, stderr = client.exec_command(cmd)

            print (stdout.read())

        client.close()

    except Exception as e:

        print (e)

if __name__ == '__main__':

    startpy()

