import json
import os
import logging
import datetime
import boto3
from botocore.exceptions import ClientError

cfn = boto3.client('cloudformation')
config = boto3.client('config')

def check_cfn(stack_name):

    required_status = "CREATE_COMPLETE"
    print(f"Checking Stack {stack_name} to see if it is in status {required_status}")

    try:
        response = cfn.describe_stacks(StackName = stack_name)
        stack_exists = response['Stacks'][0]['StackStatus'] == required_status
        stack_id = response['Stacks'][0]['StackId']
        annotation = "The " + stack_name + " stack exists and is in the " + required_status + " state."
        compliance_type = "COMPLIANT"
        print(f"{compliance_type} - {annotation}")
    except ClientError:
        annotation = "The " + stack_name + " stack does not exist or is not in the " + required_status + " state."
        compliance_type = "NON_COMPLIANT"
        stack_id = stack_name
        print(f"{compliance_type} - {annotation}")

    return {
        'compliance_resource_type': 'AWS::CloudFormation::Stack',
        'compliance_resource_id': stack_id,
        'compliance_type': compliance_type,
        'annotation': annotation
    }

def lambda_handler(event, context):
    print(f"Event: {event}")
    # decode the aws confing response
    invoking_event = json.loads(event['invokingEvent'])
    #configuration_item = invoking_event['configurationItem'] ## not used in this implementation. Throws error when not in json event.
    rule_parameters = json.loads(event['ruleParameters'])

    evaluation = check_cfn(rule_parameters['stack-name'])

    response = config.put_evaluations(
        Evaluations=[
            {
                'ComplianceResourceType': evaluation['compliance_resource_type'],
                'ComplianceResourceId': evaluation['compliance_resource_id'],
                'ComplianceType': evaluation['compliance_type'],
                'Annotation': evaluation['annotation'],
                'OrderingTimestamp': datetime.datetime.now()
            },
        ],
        ResultToken=event['resultToken'])

    print(f"Response: {response}")
    return response