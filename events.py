from __future__ import print_function  # Python 2/3 compatibility
from flask import Flask, flash, redirect, \
    render_template, request, url_for

import boto3
import json
import googlemaps
import os
import hashlib

from flask import session as login_session
from boto3.dynamodb.conditions import Key, Attr

# dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="http://localhost:8000")
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')


# Create Building Event table
def create_event_table():
    try:
        table = dynamodb.create_table(
            TableName='Events',
            KeySchema=[
                {
                    'AttributeName': 'building_name',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'building_address',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'building_name',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'building_address',
                    'AttributeType': 'S'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print("Table already exists")
        pass


# Get Building Events from Dynamodb
def get_event_response(title, address):
    # Get username from dynamodb
    table = dynamodb.Table('Events')
    building_name = title
    building_address = address
    response = table.get_item(
        Key={
            'building_name': building_name,
            'building_address': building_address
        }
    )
    return response


# Serialize Event Data
def serialize_event_data(username, fullname, age, gender, email, year, month, char_month, day, time, full_time, party_size, description):
    return {
        'username': username,
        'full_name': fullname,
        'age': age,
        'gender': gender,
        'email': email,
        'year': year,
        'month': month,
        'char_month': char_month,
        'day': day,
        'time': time,
        'full_time': full_time,
        'party_size': party_size,
        'description': description
    }


# Get Event Info Ready to Display
def get_event_info(events):
    result_array = []
    if not events:
        print('===========Event List Empty===========')
        return result_array

    else:
        for event in events:
            username = event['username']
            fullname = event['full_name']
            age = event['age']
            gender = event['gender']
            email = event['email']
            year = event['year']
            month = event['month']
            char_month = event['char_month']
            day = event['day']
            time = event['time']
            full_time = event['full_time']
            party_size = event['party_size']
            description = event['description']
            result_array.append(serialize_event_data(username, fullname, age, gender, email, year, month, char_month,
                                                     day, time, full_time, party_size, description))
        print('===========Finished Loading===========')
        print(result_array)
        return result_array


# Update User Host Item in Dynamodb
def update_host_info(username, password, host_events):
    table = dynamodb.Table('Buildings')
    username = username
    password = password
    response = table.update_item(
        Key={
            'username': username,
            'password': password
        },
        UpdateExpression="set host = :h",
        ExpressionAttributeValues={
            ':h': host_events
        }
    )


# Update User Join Item in Dynamodb
def update_joining_info(username, password, joining_events):
    table = dynamodb.Table('Buildings')
    username = username
    password = password
    response = table.update_item(
        Key={
            'username': username,
            'password': password
        },
        UpdateExpression="set joining = :g",
        ExpressionAttributeValues={
            ':g': joining_events
        }
    )


# Update Building Events Item in Dynamodb
def update_event_info(title, address, events):
    table = dynamodb.Table('Events')
    response = table.update_item(
        Key={
            'building_name': title,
            'building_address': address
        },
        UpdateExpression="set events = :e",
        ExpressionAttributeValues={
            ':e': events
        }
    )