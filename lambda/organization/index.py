import json
import os
import logging
import datetime
import boto3
from botocore.exceptions import ClientError

orgs = boto3.client('organizations')
config = boto3.client('config')

def check_scp(scp_name):

  roots = orgs.list_roots()
  root_id = roots['Roots'][0]['Id']

  print(f"Checking if SCP {scp_name} is Deployed")

  policies = orgs.list_policies(
    Filter='SERVICE_CONTROL_POLICY'
  )

  compliance_resource_id = scp_name
  compliance_type = 'NON_COMPLIANT'
  annotation = "The " + scp_name + " SCP is not deployed."

  for policy in policies['Policies']:
    if policy['Name'] == scp_name:
      print(f"Found SCP: {scp_name}")
      annotation = "The " + scp_name + " SCP is deployed but not attached to the root."
      compliance_resource_id = policy['Name'] + " (" + policy['Id'] + ")"

      is_attached = orgs.list_policies_for_target(
        Filter='SERVICE_CONTROL_POLICY',
        TargetId=root_id
      )
      for attached_policy in is_attached['Policies']:
        if attached_policy['Name'] == scp_name:
          print(f"SCP {scp_name} is attached to the root.")
          annotation = "The " + scp_name + " SCP is deployed and attached to the root."
          compliance_type = 'COMPLIANT'

  print(f"{compliance_type} - {annotation}")

  return {
      'compliance_resource_type': 'AWS::::Account',
      'compliance_resource_id': compliance_resource_id,
      'compliance_type': compliance_type,
      'annotation': annotation
  }

def check_org():

  compliance_resource_id = "Some Resource OU ID or Name"
  annotation = "This is just a test function for looking at AWS Organizations."
  compliance_type = 'NOT_APPLICABLE'

  print(f"{compliance_type} - {annotation}")

  return {
    'compliance_resource_type': 'AWS::::Account',
    'compliance_resource_id': compliance_resource_id,
    'compliance_type': compliance_type,
    'annotation': annotation
  }

def check_tag(tag_name):

  compliance_resource_id = tag_name
  annotation = "This is just a test function for looking at AWS Organizations Tag Polices."
  compliance_type = 'NOT_APPLICABLE'

  print(f"{compliance_type} - {annotation}")

  return {
    'compliance_resource_type': 'AWS::::Account',
    'compliance_resource_id': compliance_resource_id,
    'compliance_type': compliance_type,
    'annotation': annotation
  }

def lambda_handler(event, context):

  print(f"Event: {event}")
  # decode the aws confing response
  #invoking_event = json.loads(event['invokingEvent']) ## not used in this implementation. Throws error when not in json event.
  #configuration_item = invoking_event['configurationItem'] ## not used in this implementation. Throws error when not in json event.
  rule_parameters = json.loads(event['ruleParameters'])

  if rule_parameters['resource'] == 'scp':
    evaluation = check_scp(rule_parameters['scp-name'])
  if rule_parameters['resource'] == 'org':
    evaluation = check_org() #check_org(rule_parameters['org-name'])
  if rule_parameters['resource'] == 'tag':
    evaluation = check_tag(rule_parameters['tag-name'])

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
