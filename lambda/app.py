import os

# Import all the libraries needed to get started:
from lookoutvision.lookoutvision import LookoutForVision

# Training & Inferencea
input_bucket = os.getenv('s3_input_data_folder')
project_name = os.getenv('l4vProjectName')
model_version = os.getenv('l4vModelVersion')
# Inference
output_bucket = os.getenv('s3_output_data_folder')
input_prefix = 'lambdapredictinputimages/'
output_prefix = 'lambdapredictedresults/'

def lambda_handler(event, context):

    l4v = LookoutForVision(project_name=project_name)

    # Run the batch prediction
    l4v.batch_predict(
        model_version=model_version,
        input_bucket=input_bucket,
        input_prefix=input_prefix,
        output_bucket =output_bucket,
        output_prefix=output_prefix,
        content_type="image/jpeg")

    return {
        "statusCode": 200,
        "body": "Success"
    }