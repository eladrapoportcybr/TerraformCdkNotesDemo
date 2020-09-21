#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput
from imports.aws import (SnsTopic, AwsProvider, IamRole, LambdaFunction, ApiGatewayRestApi, ApiGatewayResource, ApiGatewayMethod,
                         ApiGatewayIntegration, LambdaPermission, ApiGatewayDeployment, DataAwsRegion, DataAwsCallerIdentity, S3Bucket)
import os


class MyStack(TerraformStack):
    def __init__(self, scope=Construct, ns=str):
        super().__init__(scope, ns)

        stack_prefix = "eladr_terraform_cdk_demo_"
        region = 'eu-central-1'
        AwsProvider(self, 'Aws', region=region)
        role = IamRole(self, "basic_lambda_role", description="Basic Lambda Execution Role", name=f"eladr_terraform_cdk_demo_lambda_role",
                       assume_role_policy='{"Version": "2012-10-17", "Statement": [{"Action": "sts:AssumeRole", "Principal": {"Service": "lambda.amazonaws.com"}, "Effect": "Allow", "Sid": ""}]}')

        fn = LambdaFunction(self, "lambda-hello-world", function_name="helloWorld", handler="hello_world.lambda_handler",
                            runtime="python3.7", description="A simple Hello world Lambda Function", role=role.arn, timeout=60,
                            filename=f"{os.getcwd()}/hello_world2.zip")

        api = ApiGatewayRestApi(self, "api-gateway", name="rest-api")

        resource = ApiGatewayResource(self, "api-gateway-resource", rest_api_id=api.id, parent_id=api.root_resource_id, path_part="hello")

        method = ApiGatewayMethod(self, "api-gateway-method", rest_api_id=api.id, resource_id=resource.id, http_method="GET",
                                  authorization="NONE")

        integration = ApiGatewayIntegration(self, "api-gateway-integration", rest_api_id=api.id, resource_id=resource.id,
                                            http_method=method.http_method, integration_http_method="POST", type="AWS_PROXY",
                                            uri=fn.invoke_arn, depends_on=[method])

        user_id = DataAwsCallerIdentity(self, "userId")

        LambdaPermission(self, "apigw-lambda-permission", action="lambda:InvokeFunction", principal="apigateway.amazonaws.com",
                         function_name=fn.function_name, source_arn=
                         f"arn:aws:execute-api:{region}:{user_id.account_id}:{api.id}/*/{method.http_method}{resource.path}")

        deployment = ApiGatewayDeployment(self, "api-gateway-deployment", rest_api_id=api.id, stage_name="Production",
                                          stage_description="Production Environment",
                                          description="Hello World - Production environment deployment", depends_on=[method, integration])

        bucket = S3Bucket(self, 's3_bucket', bucket='eladr-terraform-cdk-demo-bucket')
        bucket.policy = f'{{"Version": "2012-10-17", "Statement": [{{"Action": "s3:*", "Resource" : "{bucket.arn}/*", "Principal": {{"AWS": "{role.arn}"}}, "Effect": "Allow", "Sid": ""}}]}}'

        TerraformOutput(self, "endpoint", value=f"{deployment.invoke_url}/hello")
        TerraformOutput(self, "role-arn", value=role.arn)
        TerraformOutput(self, "bucket-arn", value=bucket.arn)


app = App()
MyStack(app, "terraform_cdk")

app.synth()
