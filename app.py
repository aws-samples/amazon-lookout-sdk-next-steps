#!/usr/bin/env python3
import os

import aws_cdk as cdk
import cdk_nag as cdknag
from cdk_nag import NagSuppressions, NagPackSuppression

from l4v_batch_job_prediction_cdk.l4v_batch_job_prediction_cdk_stack import L4VBatchJobPredictionCdkStack


app = cdk.App()
stack = L4VBatchJobPredictionCdkStack(app, "L4VBatchJobPredictionCdkStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=core.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=core.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )


# Simple rule informational messages
cdk.Aspects.of(app).add(cdknag.AwsSolutionsChecks())

NagSuppressions.add_stack_suppressions(stack, [
  { "id": "AwsSolutions-IAM4", "reason": "AWS Managed IAM policies have been allowed to maintain secured access with the ease of operational maintenance - however for more granular control the custom IAM policies can be used instead of AWS managed policies" },
])
NagSuppressions.add_stack_suppressions(stack, [
  { "id": "AwsSolutions-L1", "reason": "There is no non-container Lambda function" },
])

NagSuppressions.add_stack_suppressions(stack, [
  { "id": "AwsSolutions-IAM5", "reason": "AWS managed policies are allowed which sometimes uses * in the resources like - AWSGlueServiceRole has aws-glue-* . AWS Managed IAM policies have been allowed to maintain secured access with the ease of operational maintenance - however for more granular control the custom IAM policies can be used instead of AWS managed policies" },
])

app.synth()

