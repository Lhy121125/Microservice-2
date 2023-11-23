from flask import Flask, request, jsonify
import openai
import os
import boto3
from boto3.dynamodb.conditions import Attr


# Initialize a DynamoDB client with Boto3
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_DEFAULT_REGION'))  # replace 'us-east-1' with your region


# Reference your DynamoDB table
table = dynamodb.Table('microservice2_cover_letter')


app = Flask(__name__)

# Fetch your OpenAI API key from the environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')


@app.route('/')
def root():  # put application's code here
    return """This is the google app engine feature.<br> 
    We will use this to deploy cover letter service:)<br>
    To be continued..."""


@app.route('/generate_cover_letter', methods=['POST'])
def generate_cover_letter():
    # Parse "role" and "company" from the JSON body of the POST request
    data = request.json
    role = data.get('role')
    company = data.get('company')
    name = data.get('name')

    # Ensure that both "role" and "company" are provided
    if not role or not company:
        return jsonify({'error': 'The "role" and "company" fields are required.'}), 400


    try:
        # Call the OpenAI API to generate the cover letter
        response = openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"You are a professional career advisor. Please write a personalized cover letter for a {role} role at {company}. The response should be nicely formatted and easy to read",
            max_tokens=1024
        )

        # Retrieve the generated text from the response
        generated_text = response.choices[0].text.strip()

        #put to DynamoDB
        try:
            db_response = table.put_item(
                Item={
                    'cv_name': name,  # This should be a unique identifier for the item
                    'role': role,
                    'company': company,
                    'cover_letter': generated_text
                }
            )

        except Exception as e:
            error_message = f"An exception occurred at DynamoDB: {e}"
            return jsonify({'error': error_message}), 500

        # Return the generated cover letter
        return jsonify({'cover_letter': generated_text}), 200

    except Exception as e:
        # Handle general exceptions
        return jsonify({'error': str(e)}), 500

from flask import request

@app.route('/querycv', methods=['GET'])
def get_query_items():
    # Fetch query parameters
    cv_name = request.args.get('cv_name')
    role = request.args.get('role')
    company = request.args.get('company')

    # Build a filter expression based on provided arguments, use 'contains' for substring match
    filter_expression = None
    if cv_name:
        filter_expression = Attr('cv_name').contains(cv_name)
    if role:
        if filter_expression:
            filter_expression &= Attr('role').contains(role)
        else:
            filter_expression = Attr('role').contains(role)
    if company:
        if filter_expression:
            filter_expression &= Attr('company').contains(company)
        else:
            filter_expression = Attr('company').contains(company)

    # Perform the scan
    if filter_expression:
        response = table.scan(FilterExpression=filter_expression)
    else:
        return jsonify({'error': "Query Word Missing! You must provide at least ONE attribute for query!"}), 500

    return jsonify(response['Items']), 200

@app.route('/delete_cv', methods=['DELETE'])
def delete_item():
    cv_name = request.args.get('cv_name')

    if not cv_name:
        return jsonify({'error': 'cv_name is required!'}), 400

    try:
        response = table.delete_item(
            Key={
                'cv_name': cv_name
            }
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return jsonify({'message': f'Item with cv_name {cv_name} deleted successfully.'}), 200
        else:
            return jsonify({'error': f'Failed to delete item with cv_name {cv_name}.'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_template', methods=['PUT'])
def update_cover_letter():
    data = request.json
    cv_name = data.get('cv_name')
    new_company = data.get('new_company')  # User input for new company

    if not cv_name or not new_company:
        return jsonify({'error': 'cv_name and keyword1 (new company) are required'}), 400

    # Get the existing item from DynamoDB
    try:
        response = table.get_item(Key={'cv_name': cv_name})
        item = response.get('Item')
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        existing_role = item.get('role')  # Extract role from the DynamoDB item
        if not existing_role:
            return jsonify({'error': 'Role not found in the item'}), 404

        # Call OpenAI API to generate a new cover letter
        openai_response = openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"You are a professional career advisor. Please write a personalized cover letter for the role of {existing_role} at {new_company}. The response should be nicely formatted and easy to read",
            max_tokens=1024
        )
        generated_text = openai_response.choices[0].text.strip()

        # Update the item in DynamoDB
        update_response = table.update_item(
            Key={'cv_name': cv_name},
            UpdateExpression='SET cover_letter = :cover_letter, company = :new_company',
            ExpressionAttributeValues={
                ':cover_letter': generated_text,
                ':new_company': new_company
            },
            ReturnValues='UPDATED_NEW'
        )
        return jsonify({'message': 'Cover letter and company updated successfully', 'updated_attributes': update_response.get('Attributes')}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_all_cv', methods=['GET'])
def get_all_items():
    try:
        # Scan the table
        response = table.scan()

        # Retrieve the items
        items = response.get('Items', [])

        return jsonify(items), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/students', methods=['GET'])
def getStudents():
    students = f"""
    Here are the list of students:<br>
    dz2506,<br>
    qw2324,<br>
    hl3648,<br>
    ly2555,<br>
    cs4206
    """
    return students


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
