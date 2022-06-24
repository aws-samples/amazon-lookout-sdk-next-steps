import aws_cdk as cdk

from aws_cdk import (
    Duration,
    aws_kms as kms,
    aws_iam as iam,
    aws_s3 as s3,
    aws_glue as glue,
    aws_logs as logs,
    aws_cloudformation as cfn,
    aws_s3_deployment as s3deploy,
    aws_lambda as _lambda,
    aws_lambda_event_sources as eventsources,
   
)
import cdk_nag as cdknag

from constructs import Construct
from cdk_nag import NagSuppressions, NagPackSuppression

alias_name = 'l4vImagekmsAlias'
key_id = 'l4vImageKey'
key_desc = 'Key used to encrypt/decrypt images in the s3 buckets'
is_key_rotation_enabled = True


class L4VBatchJobPredictionCdkStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        cdk.CfnParameter(
            self,
            'l4vProjectName',
            type = 'String',
            description = 'Name of the lookout for vision project - it should be a string value'
        )

        cdk.CfnParameter(
            self,
            'l4vModelVersion',
            type = 'String',
            description = 'The version of lookout for vision model that you would like to use batch prediction. Please leave this as 1 if you start right at the beginning'
        )

        l4vModelVersion = cdk.Fn.sub('${l4vModelVersion}')
        l4vProjectName = cdk.Fn.sub('${l4vProjectName}')
        kms_key = self.get_kms_keys()
        buckets = self.get_s3_buckets(kms_key)
        lambda_func = self.deploy_lambda(buckets, l4vProjectName, l4vModelVersion)
        roles = self.get_iam_roles(kms_key, buckets)
        get_glue = self.get_glue(buckets, roles['glue_role'], l4vModelVersion, l4vProjectName, kms_key)
        self.get_outputs(buckets,get_glue)


    def get_kms_keys(self):
        kms_key = kms.Key(
            scope = self,
            id = key_id,
            alias = alias_name,
            enable_key_rotation = is_key_rotation_enabled,
            description = key_desc)
        
        account_root_statement = iam.PolicyStatement(
            actions = [
                'kms:Encrypt',
                'kms:Decrypt',
                'kms:ReEncrypt',
                'kms:GenerateDataKey',
                'kms:DescribeKey'
            ]
        )

        account_root_statement.add_all_resources()
        account_root_statement.add_account_root_principal()
        kms_key.add_to_resource_policy(account_root_statement)

        kms_cwlog_statement = iam.PolicyStatement(
            resources=["*"],           
            actions = [
                'kms:Encrypt',
                'kms:Decrypt',
                'kms:ReEncrypt',
                'kms:GenerateDataKey',
                'kms:DescribeKey'
            ],
            principals=[iam.ServicePrincipal("logs.amazonaws.com")],
            effect=iam.Effect.ALLOW
        )

        kms_key.add_to_resource_policy(kms_cwlog_statement)


        return kms_key

    def get_iam_roles(self, kms_key, buckets):

        policy_statement_logs = iam.PolicyStatement(
            resources = [cdk.Fn.sub('arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*')], 
            actions = [
                'logs:CreateLogGroup',
                'logs:CreateLogStream',
                'logs:PutLogEvents',
                'logs:GetLogEvents',
                'logs:AssociateKmsKey',
                ],
            effect=iam.Effect.ALLOW
        )

        policy_statement_cloudwatch = iam.PolicyStatement(
            resources = [cdk.Fn.sub('arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*')],
            actions = [
                'cloudwatch:PutMetricData',
                'cloudwatch:GetMetricData',
                'cloudwatch:ListDashboards',
                ],
            effect=iam.Effect.ALLOW
        )

        bucket_arns = []

        for b in buckets.values():
            bucket_arns.append(b.bucket_arn)
            bucket_arns.append(b.bucket_arn + '/*')

        policy_statement_s3 = iam.PolicyStatement(
            resources = bucket_arns,
            actions = [
                's3:GetBucketLocation',
                's3:GetObject',
                's3:PutObject',
                's3:ListBucket',
                's3:ListAllMyBuckets',
                's3:DeleteObject',
                ],
            effect=iam.Effect.ALLOW
        )



        policy_statement_kms = iam.PolicyStatement(
            resources = [
                kms_key.key_arn
            ],
            actions = [
                'kms:Encrypt',
                'kms:Decrypt',
                'kms:ReEncrypt',
                'kms:GenerateDataKey',
                'kms:DescribeKey',
            ],
            effect=iam.Effect.ALLOW
        )

        glue_role = iam.Role(
            id = 'glue-role',
            scope = self,
            assumed_by=iam.ServicePrincipal('glue.amazonaws.com')
        )

        glue_role.add_to_policy(policy_statement_logs)
        glue_role.add_to_policy(policy_statement_cloudwatch)
        glue_role.add_to_policy(policy_statement_s3)
        glue_role.add_to_policy(policy_statement_kms)

        glue_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                'AWSGlueConsoleFullAccess'
            )
        )

        
        glue_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                'service-role/AWSGlueServiceRole'
            )
        )


        glue_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                'AmazonLookoutVisionFullAccess'
            )
        )   
        
        roles_result = {
            'glue_role': glue_role
        }

        return roles_result

    def get_s3_buckets(self, kms_key):

        id = 'accesslogBucket'
        access_log_bucket_name = cdk.Fn.sub('access-log-l4v-${AWS::AccountId}-${AWS::Region}')        
        self.access_log_bucket = s3.Bucket(
            scope = self,
            bucket_name = access_log_bucket_name,
            id = id,
            encryption = s3.BucketEncryption.KMS,
            encryption_key = kms_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        """ cdk-nag suppression for AWS managed policies """
        NagSuppressions.add_resource_suppressions(
            self.access_log_bucket,suppressions=[
                NagPackSuppression(
                    id= "AwsSolutions-S1",
                    reason= "S3 access logging not required for access_log_bucket itself.",
                    )
                    ]
                )


        id = 'inputImageDataBucket'
        input_image_bucket_name = cdk.Fn.sub('input-image-${AWS::AccountId}-${AWS::Region}')        
        self.input_image_example = s3.Bucket(
            scope = self,
            bucket_name = input_image_bucket_name,
            id = id,
            encryption = s3.BucketEncryption.KMS,
            encryption_key = kms_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            server_access_logs_bucket=self.access_log_bucket,
            enforce_ssl=True,
        )

        id = 'predictedResultDataBucket'
        pred_result_bucket_name = cdk.Fn.sub('predicted-result-${AWS::AccountId}-${AWS::Region}')        
        self.pred_result_example = s3.Bucket(
            scope = self,
            bucket_name = pred_result_bucket_name,
            id = id,
            encryption = s3.BucketEncryption.KMS,
            encryption_key = kms_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            server_access_logs_bucket=self.access_log_bucket,
            enforce_ssl=True,
        )

        
        glue_helpers_bucket_id = 'GlueHelpersBucket'

        glue_helpers_bucket = s3.Bucket(
            scope = self,
            bucket_name = cdk.Fn.sub('lookoutforvision-glue-helpers-${AWS::AccountId}-${AWS::Region}'),
            id = glue_helpers_bucket_id,
            versioned = True,
            encryption = s3.BucketEncryption.KMS,
            encryption_key = kms_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            server_access_logs_bucket=self.access_log_bucket,
            enforce_ssl=True,
        )

        l4v_whlFile_bucket_id = 'l4vWhlFileBucket'

        l4v_whlFile_bucket = s3.Bucket(
            scope = self,
            bucket_name = cdk.Fn.sub('lookoutforvision-whlfile-${AWS::AccountId}-${AWS::Region}'),
            id = l4v_whlFile_bucket_id,
            versioned = True,
            encryption = s3.BucketEncryption.KMS,
            encryption_key = kms_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            server_access_logs_bucket=self.access_log_bucket,
            enforce_ssl=True,
        )

        # Upload glue scripts to the glue helper bucket
        s3uploadGlue = s3deploy.BucketDeployment(self, "DeployGlueJobScript",
                       sources=[s3deploy.Source.asset("./external_assets/glue-scripts/")],
                       destination_bucket= glue_helpers_bucket,
                       destination_key_prefix="glue-scripts"
                       )

        # Upload sample input images to the input bucket
        s3uploadImage = s3deploy.BucketDeployment(self, "SampleInputImages",
                       sources=[s3deploy.Source.asset("./data")],
                       destination_bucket=self.input_image_example,
                       destination_key_prefix="inputimages"
                       )


        result = {
            'input_image_bucket': self.input_image_example,
            'pred_result_bucket': self.pred_result_example,
            'glue_helpers_bucket': glue_helpers_bucket,
            'l4v_whlFile_bucket': l4v_whlFile_bucket,
        }

        return result

    def get_glue(self, buckets, iam_role, l4vModelVersion, l4vProjectName, kms_key):

        sc_name = 'glue_security_configuration_l4vjobs'
        sc = glue.CfnSecurityConfiguration(
            scope = self,
            id = sc_name,
            name = sc_name,
            encryption_configuration=glue.CfnSecurityConfiguration.EncryptionConfigurationProperty(
                s3_encryptions=[
                    glue.CfnSecurityConfiguration.S3EncryptionProperty(
                        s3_encryption_mode='SSE-KMS',
                        kms_key_arn=kms_key.key_arn
                    )
                ],
                cloud_watch_encryption=glue.CfnSecurityConfiguration.CloudWatchEncryptionProperty(
                    cloud_watch_encryption_mode='SSE-KMS',
                    kms_key_arn=kms_key.key_arn
                ),
                job_bookmarks_encryption=glue.CfnSecurityConfiguration.JobBookmarksEncryptionProperty(
                    job_bookmarks_encryption_mode='CSE-KMS',
                    kms_key_arn=kms_key.key_arn
                )
            )
        )

        group_name = 'glue_jobs_l4v_batch_predict'
        log_group = logs.LogGroup(
            scope = self,
            log_group_name = group_name,
            id = group_name
        )

        glue_job_scripts = cdk.Fn.sub('s3://lookoutforvision-glue-helpers-${AWS::AccountId}-${AWS::Region}/glue-scripts/batch_prediction.py')
        TempDir = cdk.Fn.sub('s3://lookoutforvision-glue-helpers-${AWS::AccountId}-${AWS::Region}/')
        extra_python_library_location = cdk.Fn.sub('s3://lookoutforvision-whlfile-${AWS::AccountId}-${AWS::Region}/lookoutvision-0.1.5-py3-none-any.whl')
        input_image_bucket = buckets['input_image_bucket'].bucket_name
        pred_result_bucket = buckets['pred_result_bucket'].bucket_name

        l4v_batch_pred_job = glue.CfnJob(self, "Myl4vBatchPredJob", 
            command=glue.CfnJob.JobCommandProperty(
                name = 'pythonshell',
                script_location = glue_job_scripts,
                python_version= '3'
            ),
            role=iam_role.role_arn,
            max_capacity = 1,
            glue_version= "1.0",
            security_configuration= sc.name,
            default_arguments= {
                    '--enable-glue-datacatalog': '',
                    '--continuous-log-logGroup': log_group.log_group_name,
                    '--enable-continuous-cloudwatch-log': 'true',
                    '--enable-continuous-log-filter': 'true',
                    '--enable-metrics': 'true',
                    '--job-bookmark-option': 'job-bookmark-enable',
                    '--TempDir': TempDir,
                    '--s3_input_data_folder': input_image_bucket,
                    '--s3_output_data_folder': pred_result_bucket,
                    '--extra-py-files': extra_python_library_location,
                    '--l4vProjectName': l4vProjectName,
                    '--l4vModelVersion': l4vModelVersion
                }

        )

        workflow_name = 'batch-prediction-workflow'
        workflow = glue.CfnWorkflow(
            scope = self,
            id = 'BatchPredictionWorkflow',
            name = workflow_name,
        )

        trigger_name = glue.CfnTrigger(
            scope = self,
            id = 'trigger00',
            workflow_name = workflow.ref,
            type = 'ON_DEMAND',
            name = 'trigger-l4v-batch-prediction',
            actions = [
                glue.CfnTrigger.ActionProperty(
                    job_name = l4v_batch_pred_job.ref
                ),
           ],
        )

        result = {
            'glue_job_name': l4v_batch_pred_job.ref,
            'glue_workflow_name': workflow.ref,
            'glue_wf_trigger_name': trigger_name.ref
        }
        return result


    def get_outputs(self,buckets,get_glue):
        cfn_input_image_bucket = cdk.CfnOutput(self, "input_image_bucket", value=buckets['input_image_bucket'].bucket_name, description="input_image_bucket")
        cfn_pred_result_bucket = cdk.CfnOutput(self, "pred_result_bucket", value=buckets['pred_result_bucket'].bucket_name, description="pred_result_bucket")
        cfn_glue_script_bucket = cdk.CfnOutput(self, "glue_script_bucket", value=buckets['glue_helpers_bucket'].bucket_name, description="glue_script_bucket")
        cfn_l4v_whlFile_bucket = cdk.CfnOutput(self, "l4v_whlFile_bucket", value=buckets['l4v_whlFile_bucket'].bucket_name, description="l4v_pythonLibrary_bucket")
        cfn_glue_job_name = cdk.CfnOutput(self, "glue_job_name", value=get_glue['glue_job_name'], description="Name of the Glue job to predict the images in a batch")
        cfn_glue_workflow_name = cdk.CfnOutput(self, "glue_workflow_name", value=get_glue['glue_workflow_name'],description="Name of the Glue Workflow that you can schedule accordingly- currently this is on-demand. You may schedule it as per your requirement like daily, weekly etc")
        cfn_glue_wf_trigger_name = cdk.CfnOutput(self, "glue_wf_trigger_name", value=get_glue['glue_wf_trigger_name'],description="Name of the Glue trigger which starts the Glue workflow - batch-prediction-workflow")


    def deploy_lambda(self, buckets, l4vProjectName, l4vModelVersion):
        # lambda
        lambda_environ = {
            's3_input_data_folder': buckets['input_image_bucket'].bucket_name,
            'l4vProjectName': l4vProjectName,
            'l4vModelVersion': l4vModelVersion,
            's3_output_data_folder': buckets['pred_result_bucket'].bucket_name,
        }
        # Defines an AWS Lambda resource
        lambda_func = _lambda.DockerImageFunction(
            self,
            id="lookout-lambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda"),
            environment=lambda_environ,
            timeout=Duration.minutes(2),
        )
        
        # lambda policies
        self.input_image_example.grant_read_write(lambda_func)
        self.pred_result_example.grant_read_write(lambda_func)



        lambdarole = lambda_func.role


        #lambdarole.add_to_policy(policy_statement_lookoutvision)
        lambdarole.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                'AmazonLookoutVisionFullAccess'
            )
        )



        # add event trigger to the lambda
        lambda_func.add_event_source(eventsources.S3EventSource(self.input_image_example,
            events=[s3.EventType.OBJECT_CREATED],
            filters=[s3.NotificationKeyFilter(prefix="lambdapredictinputimages/")]
        ))

        return True        
