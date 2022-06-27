# This section makes sure you are using the latest boto3 version
import sys
# import upgraded boto3 since by default boto3 1.9 is in-built to AWS Glue python shell job and this 1.9 version needs to be removed. 
# So upgrading boto3 version as per this --> https://repost.aws/questions/QUGL8ViiigQwGdR8gj0L0anw?threadID=327010
sys.path.insert(0, '/glue/lib/installation')
keys = [k for k in sys.modules.keys() if 'boto' in k]
for k in keys:
    if 'boto' in k:
        del sys.modules[k]
import boto3

from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ['s3_input_data_folder', 's3_output_data_folder', 'l4vProjectName' , 'l4vModelVersion'])

# Training & Inferencea
input_bucket = args['s3_input_data_folder']
project_name = args['l4vProjectName']
model_version = args['l4vModelVersion']

# Inference
output_bucket = args['s3_output_data_folder']
input_prefix = 'inputimages/'
output_prefix = 'predictedresults/'

# Import lookout python library - needed to get started:
from lookoutvision.lookoutvision import LookoutForVision

l4v = LookoutForVision(project_name=project_name)

# Run the batch prediction
l4v.batch_predict(
    model_version=model_version,
    input_bucket=input_bucket,
    input_prefix=input_prefix,
    output_bucket =output_bucket,
    output_prefix=output_prefix,
    content_type="image/jpeg")