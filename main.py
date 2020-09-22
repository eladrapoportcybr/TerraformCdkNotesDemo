#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput
from imports.aws import (SnsTopic, AwsProvider, IamRole, LambdaFunction, ApiGatewayRestApi, ApiGatewayResource, ApiGatewayMethod,
                         ApiGatewayIntegration, LambdaPermission, ApiGatewayDeployment, DataAwsRegion, DataAwsCallerIdentity, S3Bucket)
import os
stack_prefix = "eladr_terraform_cdk_demo_"
region = 'eu-central-1'


def add_gateway_method(scope: Construct, http_method: str, handler: str, api_gw: ApiGatewayRestApi, resource, role_arn: str, user_id):
    suffix = handler[:3]
    fn = LambdaFunction(scope, f"{stack_prefix}lambda-{suffix}", function_name=f"{stack_prefix}lambda{suffix}",
                        handler=f"notes_handler.{handler}",
                        runtime="python3.7", role=role_arn, timeout=60,
                        filename=f"{os.getcwd()}/notes_handler.zip")
    method = ApiGatewayMethod(scope, f"api-gateway-method-{suffix}", rest_api_id=api_gw.id, resource_id=resource.id, http_method=http_method,
                              authorization="NONE")
    integration = ApiGatewayIntegration(scope, f"api-gateway-integration-{suffix}", rest_api_id=api_gw.id, resource_id=resource.id,
                                        http_method=method.http_method, integration_http_method="POST", type="AWS_PROXY",
                                        uri=fn.invoke_arn, depends_on=[method])
    LambdaPermission(scope, f"{stack_prefix}lambda-permission-{suffix}", action="lambda:InvokeFunction", principal="apigateway.amazonaws.com",
                     function_name=fn.function_name, source_arn=
                     f"arn:aws:execute-api:{region}:{user_id.account_id}:{api_gw.id}/*/{method.http_method}{resource.path}")
    return [method, integration]


class NotesStack(TerraformStack):
    def __init__(self, scope=Construct, ns=str):
        super().__init__(scope, ns)

        user_id = DataAwsCallerIdentity(self, "userId")
        AwsProvider(self, 'Aws', region=region)
        role = IamRole(self, "basic_lambda_role", description="Basic Lambda Execution Role", name=f"{stack_prefix}lambda_role",
                       assume_role_policy='{"Version": "2012-10-17", "Statement": [{"Action": "sts:AssumeRole", "Principal": {"Service": "lambda.amazonaws.com"}, "Effect": "Allow", "Sid": ""}]}')
        api = ApiGatewayRestApi(self, "api-gateway", name="rest-api")
        resource = ApiGatewayResource(self, f"api-gateway-resource", rest_api_id=api.id, parent_id=api.root_resource_id, path_part="notes")

        get_notes = add_gateway_method(self, "GET", "get_notes_handler", api, resource, role.arn, user_id)
        add_note = add_gateway_method(self, "POST", "add_note_handler", api, resource, role.arn, user_id)
        delete_note = add_gateway_method(self, "DELETE", "delete_note_handler", api, resource, role.arn, user_id)

        deployment = ApiGatewayDeployment(self, f"{stack_prefix}api-gateway-deployment", rest_api_id=api.id, stage_name="dev",
                                          stage_description="Production Environment", depends_on=get_notes + add_note + delete_note)

        bucket_name = 'eladr-terraform-cdk-demo-bucket'
        bucket = S3Bucket(self, 's3_bucket', bucket=bucket_name, force_destroy=True)
        bucket.policy = f'{{"Version": "2012-10-17", "Statement": [{{"Action": "s3:*", "Resource" : "arn:aws:s3:::{bucket_name}/*", "Principal": {{"AWS": "{role.arn}"}}, "Effect": "Allow", "Sid": ""}}]}}'

        TerraformOutput(self, "endpoint", value=f"{deployment.invoke_url}")
        TerraformOutput(self, "bucket-arn", value=bucket.arn)


app = App()
NotesStack(app, "terraform_cdk")

app.synth()
