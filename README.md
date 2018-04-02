
This script creates VPCs and makes multiple VPC peering connection.



#Installation Guide


 ./entrypoint.sh -e <environment> -m <VPC main id> -i <AMI ID> -n <VPC name> -c <VPC CIDR> -s <VPC SUBNET>

   -   environment : which stores key-value paired environment values, such as AWS_ACCESS_KEY, AWS_ACCOUNT_ID and so on.
   -   VPC main id : which is ID of main VPC (ZIO VPC main). e.g "vpc-4bbc2023"
   -   AMI ID      : which is AMI of new VPC to be created. e.g "ami-25615740"
   -   VPC name    : which is the name of VPC to be created. e.g "vpc-zio-sub-1"
   -   VPC CIDR    : which is the CIDR of VPC to be created. e.g "18.0.0.0/16"
   -   VPC SUBNET  : which is the SUBNET of VPC to be created. e.g "18.0.0.0/24"


#One VPC peered with multiple VPCs

 Sample Instruction
 
 - ./entrypoint.sh -e dev -m "vpc-05c3858734b8f1d7c" -i "ami-25615740" -n "zio-vpc-sub-1" -c "173.0.0.0/16" -s "173.2.0.0/24"

 - ./entrypoint.sh -e dev -m "vpc-05c3858734b8f1d7c" -i "ami-25615740" -n "zio-vpc-sub-2" -c "174.0.0.0/16" -s "174.1.0.0/24"