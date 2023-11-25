from flask import Flask, request, jsonify
import openai
import os
import boto3
from boto3.dynamodb.conditions import Key

# Initialize a DynamoDB client with Boto3
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_DEFAULT_REGION'))  # replace 'us-east-1' with your region


# Reference your DynamoDB table
table = dynamodb.Table('micro2_cv_template')


app = Flask(__name__)

# Fetch your OpenAI API key from the environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')


@app.route('/')
def root():  # put application's code here
    return """This is the google app engine feature.<br> 
    We will use this to deploy cover letter service:)<br>
    To be continued..."""


@app.route('/<user_id>/generate_cover_letter', methods=['POST'])
def generate_cover_letter(user_id):
    # Parse "role" and "company" from the JSON body of the POST request
    data = request.json
    role = data.get('role')
    company = data.get('company')
    template_name = data.get('template_name')

    # Ensure that both "role" and "company" are provided
    if not role or not company:
        return jsonify({'error': 'The "role" and "company" fields are required.'}), 400


    try:
        # Call the OpenAI API to generate the cover letter
        response = openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"You are a professional career advisor. Please write a personalized cover letter as a new grad from college for a {role} role at {company}. The response should be nicely formatted and easy to read",
            max_tokens=1024
        )

        # Retrieve the generated text from the response
        generated_text = response.choices[0].text.strip()

        #put to DynamoDB
        try:
            db_response = table.put_item(
                Item={
                    'user_id': user_id,  # This should be a unique identifier for each student
                    'template_name': template_name,  # This should be a unique identifier for the item
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


@app.route('/<user_id>/querycv/<template_name>', methods=['GET'])
def get_query_items(user_id,template_name):
    try:
        # Query the DynamoDB table for the specified user_id and cv_name
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id) &Key('template_name').eq(template_name)
        )

        # Check if items were found
        items = response.get('Items', [])
        if not items:
            return jsonify({'message': 'No items found for the provided user_id and template_name'}), 404

        # Return the found items
        return jsonify(items), 200

    except Exception as e:
        # Handle any exceptions that occur during the query
        return jsonify({'error': str(e)}), 500

@app.route('/<user_id>/delete_cv/<template_name>', methods=['DELETE'])
def delete_item(user_id,template_name):
    try:
        # Delete the item from the DynamoDB table
        response = table.delete_item(
            Key={
                'user_id': user_id,
                'template_name': template_name
            }
        )

        # Check the response status code
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return jsonify({'message': f'Item with user_id {user_id} and template_name {template_name} deleted successfully.'}), 200
        else:
            return jsonify({'error': 'Failed to delete item.'}), 500

    except Exception as e:
        # Handle any exceptions that occur during deletion
        return jsonify({'error': str(e)}), 500

@app.route('/<user_id>/update_template/<template_name>', methods=['PUT'])
def update_cover_letter(user_id,template_name):
    data = request.json

    new_company = data.get('new_company')  # User input for new company

    if not new_company:
        return jsonify({'error': 'new_company is required'}), 400

    # Get the existing item from DynamoDB
    try:
        response = table.get_item(Key={'user_id': user_id,'template_name': template_name})
        item = response.get('Item')
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        existing_role = item.get('role')  # Extract role from the DynamoDB item
        if not existing_role:
            return jsonify({'error': 'Role not found in the item'}), 404

        # Call OpenAI API to generate a new cover letter
        openai_response = openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"You are a professional career advisor. Please write a personalized cover letter as a new grad from college for the role of {existing_role} at {new_company}. The response should be nicely formatted and easy to read",
            max_tokens=1024
        )
        generated_text = openai_response.choices[0].text.strip()

        # Update the item in DynamoDB
        update_response = table.update_item(
            Key={'user_id':user_id,'template_name': template_name},
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

@app.route('/<user_id>/get_all_cv', methods=['GET'])
def get_all_items(user_id):
    try:
        # Query the DynamoDB table for items with the specified user_id
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )

        items = response.get('Items', [])

        return jsonify(items), 200

    except Exception as e:
        # Handle any exceptions that occur during the query
        return jsonify({'error': str(e)}), 500

@app.route('/<user_id>/get_template_count', methods=['GET'])
def get_template_count(user_id):
    try:
        # Query the DynamoDB table for items with the specified user_id
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )

        items = response.get('Items', [])

        return jsonify({'template_count': len(items)}), 200

    except Exception as e:
        # Handle any exceptions that occur during the query
        return jsonify({'error': str(e)}), 500
'''
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
'''

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
