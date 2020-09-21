#!/usr/bin/env python

from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput
from imports.aws import (SnsTopic,
                         AwsProvider,
                         IamRole,
                         LambdaFunction,
                         ApiGatewayRestApi,
                         ApiGatewayResource,
                         ApiGatewayMethod,
                         ApiGatewayIntegration,
                         LambdaPermission,
                         ApiGatewayDeployment,
                         DataAwsRegion,
                         DataAwsCallerIdentity,
                         S3Bucket)

import os
from imports.terraform_aws_modules.vpc.aws import Vpc


class MyStack(TerraformStack):
    def __init__(self, scope=Construct, ns=str):
        super().__init__(scope, ns)

        region = 'eu-central-1'
        AwsProvider(self, 'Aws', region=region)

        # Vpc(self, 'cdktf-eladr-test-vpc',
        #     name='cdktf-eladr-test-vpc',
        #     cidr='10.0.0.0/16',
        #     azs=["us-east-1a", "us-east-1b"],
        #     public_subnets=["10.0.1.0/24", "10.0.2.0/24"]
        #     )
        # SnsTopic(self, 'cdktf-eladr-test-sns-topic', display_name='cdktf-eladr-test-sns-topic')

        # S3Bucket(self, 's3_bucket', bucket='eladr-terraform-cdk-demo-bucket')
        #
        # role = IamRole(self, "basic_lambda_role", description="Basic Lambda Execution Role",
        #                assume_role_policy='{"Version": "2012-10-17", "Statement": [{"Action": "sts:AssumeRole", "Principal": {"Service": '
        #                                   '"lambda.amazonaws.com"}, "Effect": "Allow", "Sid": ""}, '
        #                                   '{"Action": "s3:*", "Resource": [arn:aws:s3:::eladr-terraform-cdk-demo-bucket/*], "Effect": "Allow", "Sid": ""}]}')

        role = IamRole(self, "basic_lambda_role", description="Basic Lambda Execution Role",
                       assume_role_policy='{"Version": "2012-10-17", "Statement": [{"Action": "sts:AssumeRole", "Principal": {"Service": "lambda.amazonaws.com"}, "Effect": "Allow", "Sid": ""}]}')

        fn = LambdaFunction(self, "lambda-hello-world",
                            function_name="helloWorld",
                            handler="hello_world.lambda_handler",
                            runtime="python3.7",
                            description="A simple Hello world Lambda Function",
                            role=role.arn,
                            timeout=60,
                            filename=f"{os.getcwd()}/hello_world.zip",
                            )

        api = ApiGatewayRestApi(self, "api-gateway",
                                name="rest-api")

        resource = ApiGatewayResource(self, "api-gateway-resource",
                                      rest_api_id=api.id,
                                      parent_id=api.root_resource_id,
                                      path_part="hello"
                                      )

        method = ApiGatewayMethod(self, "api-gateway-method",
                                  rest_api_id=api.id,
                                  resource_id=resource.id,
                                  http_method="GET",
                                  authorization="NONE",
                                  )

        integration = ApiGatewayIntegration(self, "api-gateway-integration",
                                            rest_api_id=api.id,
                                            resource_id=resource.id,
                                            http_method=method.http_method,
                                            integration_http_method="POST",
                                            type="AWS_PROXY",
                                            uri=fn.invoke_arn,
                                            depends_on=[method]
                                            )

        region = DataAwsRegion(self, "region")
        user_id = DataAwsCallerIdentity(self, "userId")

        LambdaPermission(self, "apigw-lambda-permission",
                         action="lambda:InvokeFunction",
                         principal="apigateway.amazonaws.com",
                         function_name=fn.function_name,
                         source_arn=
                         f"arn:aws:execute-api:{region.name}:{user_id.account_id}:{api.id}/*/{method.http_method}{resource.path}"
                         )

        deployment = ApiGatewayDeployment(self, "api-gateway-deployment",
                                          rest_api_id=api.id,
                                          stage_name="Production",
                                          stage_description="Production Environment",
                                          description="Hello World - Production environment deployment",
                                          depends_on=[method, integration]
                                          )

        TerraformOutput(self, "endpoint",
                        value=f"{deployment.invoke_url}/hello")


app = App()
MyStack(app, "terraform_cdk")

app.synth()
