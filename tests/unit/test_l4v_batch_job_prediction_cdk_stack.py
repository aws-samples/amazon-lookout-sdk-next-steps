# from aws_cdk import (
#         core,
#         assertions
#     )

# from l4v_batch_job_prediction_cdk.l4v_batch_job_prediction_cdk_stack import L4VBatchJobPredictionCdkStack


# example tests. To run these tests, uncomment this file along with the example
# resource in l4v_batch_job_prediction_cdk/l4v_batch_job_prediction_cdk_stack.py
def test_sqs_queue_created():
#     app = core.App()
#     stack = L4VBatchJobPredictionCdkStack(app, "l4v-batch-job-prediction-cdk")
#     template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
  pass


import aws_cdk as core
import aws_cdk.assertions as assertions
from l4v_batch_job_prediction_cdk.l4v_batch_job_prediction_cdk_stack import L4VBatchJobPredictionCdkStack


def test_glue_jobs_created():
    app = core.App()
    stack = L4VBatchJobPredictionCdkStack(app, "L4VBatchJobPredictionCdkStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::Glue::Job", 1)

def test_glue_trigger_created():
    app = core.App()
    stack = L4VBatchJobPredictionCdkStack(app, "L4VBatchJobPredictionCdkStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::Glue::Trigger", 1)

def test_glue_workflow_created():
    app = core.App()
    stack = L4VBatchJobPredictionCdkStack(app, "L4VBatchJobPredictionCdkStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::Glue::Workflow", 1)

def test_iam_policies_created():
    app = core.App()
    stack = L4VBatchJobPredictionCdkStack(app, "L4VBatchJobPredictionCdkStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::IAM::Policy", 4)

def test_iam_roles_created():
    app = core.App()
    stack = L4VBatchJobPredictionCdkStack(app, "L4VBatchJobPredictionCdkStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::IAM::Role", 4)

def test_kms_alias_created():
    app = core.App()
    stack = L4VBatchJobPredictionCdkStack(app, "L4VBatchJobPredictionCdkStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::KMS::Alias", 1)

def test_kms_key_created():
    app = core.App()
    stack = L4VBatchJobPredictionCdkStack(app, "L4VBatchJobPredictionCdkStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::KMS::Key", 1)

def test_lambda_functions_created():
    app = core.App()
    stack = L4VBatchJobPredictionCdkStack(app, "L4VBatchJobPredictionCdkStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::Lambda::Function", 3)

def test_lambda_layers_created():
    app = core.App()
    stack = L4VBatchJobPredictionCdkStack(app, "L4VBatchJobPredictionCdkStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::Lambda::LayerVersion", 3)

def test_s3_buckets_created():
    app = core.App()
    stack = L4VBatchJobPredictionCdkStack(app, "L4VBatchJobPredictionCdkStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::S3::Bucket", 4)