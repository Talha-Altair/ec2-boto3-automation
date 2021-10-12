import os
import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = "ap-southeast-1"

KEY_PAIR_NAME = "tact-ec2-key-pair"

PEM_FILE_DIR = "./pem_files"

AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]

AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]

ec2_client = boto3.client(
                        "ec2",
                        region_name= AWS_REGION,
                        aws_access_key_id = AWS_ACCESS_KEY_ID,
                        aws_secret_access_key = AWS_SECRET_ACCESS_KEY
                        )

def create_key_pair():

    key_pair = ec2_client.create_key_pair(KeyName = KEY_PAIR_NAME)

    private_key = key_pair["KeyMaterial"]

    with os.fdopen(os.open(f"{PEM_FILE_DIR}/{KEY_PAIR_NAME}.pem", os.O_WRONLY | os.O_CREAT, 0o400), "w+") as handle:

        handle.write(private_key)

def create_instance():

    instances = ec2_client.run_instances(

        ImageId         = "ami-0d058fe428540cd89",
        MinCount        = 1,
        MaxCount        = 1,
        InstanceType    = "t2.micro",
        KeyName         = KEY_PAIR_NAME

    )

    instance_id = instances["Instances"][0]["InstanceId"]

    return instance_id

def get_public_ip(instance_id):

    reservations = ec2_client.describe_instances(InstanceIds=[instance_id]).get("Reservations")

    for reservation in reservations:
        for instance in reservation['Instances']:
            ip_address = instance.get("PublicIpAddress")

    return ip_address

def startpy():

    # create_key_pair()

    # instance_id = create_instance()

    # print(instance_id)

    # ip_address = get_public_ip(instance_id)

    # print(ip_address)

    print("Done")

if __name__ == '__main__':

    startpy()

