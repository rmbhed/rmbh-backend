import boto3
import json
import os
from urllib.parse import urlparse

# Initialize the DynamoDB resource outside the handler for better performance
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DATABASE_NAME'])

def get_path(event):
    # 1. Check Query String (?page=/about)
    query_params = event.get('queryStringParameters') or {}
    page_path = query_params.get('page')

    # 2. If missing, check the Referer header (must be lowercase 'referer')
    if not page_path:
        headers = event.get('headers') or {}
        referer = headers.get('referer')
        if referer:
            # Extracts just "/index.html" from "https://rmbh.me/index.html"
            page_path = urlparse(referer).path

    # 3. Clean up and Fallback
    # If it's empty or just a slash, call it 'home'
    if not page_path or page_path == "/":
        page_path = "/index"
        
    print(f"Final resolved path: {page_path}")
    return page_path

def lambda_handler(event, context):
    try:
        # Get the path from the API Gateway event
        page_path = get_path(event)
        # Try to get and increment the current count for this path
        response = table.update_item(
            Key={'path_id': page_path}, 
            UpdateExpression="ADD visitor_count :inc",
            ExpressionAttributeValues={':inc': 1},
            ReturnValues="UPDATED_NEW"
        )
        return {
            'statusCode': 200,
            'headers': {
            'Access-Control-Allow-Origin': 'https://rmbh.me',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                },
            'body': str(response['Attributes']['visitor_count'])
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 200,
            'headers': {
            'Access-Control-Allow-Origin': 'https://rmbh.me',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                },
            'body': '-'
        }
