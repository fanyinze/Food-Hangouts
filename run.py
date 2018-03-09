from __future__ import print_function  # Python 2/3 compatibility
from flask import Flask, flash, redirect, \
    render_template, request, url_for

import boto3
import json
import googlemaps
import os
import hashlib
import dateutil.parser
from events import *
from ast import literal_eval
from flask import session as login_session
from boto3.dynamodb.conditions import Key, Attr

#dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="http://localhost:8000")
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
app = Flask(__name__)
app.secret_key = '#super secret key#'

gmaps = googlemaps.Client(key='#your key#')
password_key = '#your password key#'


# Create route and function to display home page
@app.route('/')
def home():
    # delete_table()
    create_table()
    create_event_table()
    if not login_session.get('logged_in'):
        return render_template('login.html', login_session=login_session)
    else:
        return redirect(url_for('userRestaurant',
                                user_id=login_session['user_id']))


# Create route and function to display signup page
@app.route('/signup', methods=['GET', 'POST'])
def showSignup():
    if request.method == 'POST':
        login_session['username'] = str(request.form['username'])
        login_session['password'] = str(request.form['password'])
        email = str(request.form['email'])
        gender = str(request.form['gender'])
        age = str(request.form['age'])
        first_name = str(request.form['firstname'])
        last_name = str(request.form['lastname'])
        confirm_password = str(request.form['confirm_password'])

        if login_session['username'] == "" or login_session['password'] == "":
            flash("Username/Password can't be empty")
            return redirect(url_for('showSignup'))

        if first_name == "" or last_name == "":
            flash("Username/Password can't be empty")
            return redirect(url_for('showSignup'))

        if confirm_password != login_session['password']:
            flash("Password does not match the confirm password")
            return redirect(url_for('showSignup'))

        username = login_session['username']
        hashed_password = hashed(login_session['password'])
        login_session['password'] = hashed_password

        response = get_response(username, login_session['password'])

        for x, y in response.items():
            print(x, y)

        if 'Item' in response:
            flash("user already exists")
            return redirect(url_for('showSignup'))

        else:
            global password_key
            password_key = hashed_password
            table = dynamodb.Table('Buildings')
            response = table.put_item(
                Item={
                    'username': username,
                    'password': hashed_password,
                    'firstname': first_name,
                    'lastname': last_name,
                    'age': age,
                    'gender': gender,
                    'email': email,
                    'buildings': {
                    },
                    'joining': [

                    ],
                    'host': [

                    ]
                }
            )
            login_session['logged_in'] = True
            login_session['user_id'] = username
            return redirect(url_for('userRestaurant', user_id=username))

    elif request.method == 'GET':
        return render_template('signup.html', login_session=login_session)


# Create route and function to display login page
@app.route('/login', methods=['POST'])
def do_admin_login():
    login_session['username'] = str(request.form['username'])
    login_session['password'] = str(request.form['password'])

    if login_session['username'] == "" or login_session['password'] == "":
        flash("Username/Password can't be empty")
        return redirect(url_for('home'))

    username = login_session['username']
    hashed_password = hashed(login_session['password'])

    login_session['password'] = hashed_password

    response = get_response(username, login_session['password'])

    if 'Item' in response:
        global password_key
        password_key = hashed_password
        login_session['logged_in'] = True
        login_session['user_id'] = username
        return redirect(url_for('userRestaurant', user_id=username))
    else:
        flash('Incorrect username or password!')
        return render_template('login.html', login_session=login_session)


# Create route and function to display logout page
@app.route("/logout")
def logout():
    global password_key
    password_key = ""
    login_session['logged_in'] = False
    del login_session['username']
    del login_session['password']
    del login_session['user_id']
    return redirect(url_for('home'))


# Create route and function to display all buildings under a layout
@app.route('/restaurant/<string:user_id>', methods=['GET', 'POST'])
def userRestaurant(user_id):
    if not login_session.get('logged_in'):
        return render_template('login.html', login_session=login_session)

    if login_session['user_id'] != user_id:
        return render_template('showwarning.html', user_id=login_session['user_id'])

    global password_key

    user = user_id
    # password = password_key
    password = login_session['password']
    response = get_response(user, password)

    # ===== Get User Info =====
    firstname = response['Item']['firstname']
    lastname = response['Item']['lastname']
    age = response['Item']['age']
    gender = response['Item']['gender']

    # ===== Get Building List =====
    buildings = response['Item']['buildings']
    result = get_building_info(buildings)

    # ===== Get Event List =====
    joining_event = response['Item']['joining']

    # ===== Check if each join event exist on Event table =====
    for each_join in joining_event:
        title = each_join['title']
        address = each_join['address']
        full_time = each_join['full_time']
        host = each_join['host']
        event_response = get_event_response(title, address)
        event_exist = False
        for each_event in event_response['Item']['events']:
            if full_time == each_event['full_time'] and host == each_event['full_name']:
                event_exist = True
            else:
                pass
        if not event_exist:
            each_join['description'] = 'cancelled'

    print('=====Join Events:=====')
    print(joining_event)
    print('==========')
    host_event = response['Item']['host']
    print('=====Host Events:=====')
    print(host_event)
    print('==========')

    return render_template('index.html', result=result, user=user, firstname=firstname.title(), buildings=result,
                           join=joining_event, host=host_event)


@app.route('/restaurant/<string:user_id>/new', methods=['GET', 'POST'])
def newRestaurant(user_id):
    if not login_session.get('logged_in'):
        return render_template('login.html', login_session=login_session)

    if login_session['user_id'] != user_id:
        return render_template('showwarning.html', user_id=login_session['user_id'])

    if request.method == 'POST':
        requestString = request.form['name'] + request.form['street'] + ',' + request.form['city']
        places_result = gmaps.places(requestString)

        print(places_result)
        if not places_result["results"]:
            print('======Location Not Found=====')
            flash("Location not found, please specify the street address or try different location")
            return redirect(url_for('userRestaurant', user_id=user_id))

        print('======Loading Building Info from Google Map======')
        print(places_result["results"][0])

        if 'name' not in places_result["results"][0]:
            name = 'Not Found'
        else:
            name = places_result["results"][0]['name']

        if 'rating' not in places_result["results"][0]:
            rating = 'Not Found'
        else:
            rating = places_result["results"][0]["rating"]

        if 'photo_reference' not in places_result["results"][0]['photos'][0]:
            photo_reference = 'Not Found'
        else:
            photo_reference = places_result["results"][0]['photos'][0]['photo_reference']

        location = places_result["results"][0]['geometry']['location']
        address = places_result["results"][0]['formatted_address'].split(',')

        full_reference = photo_reference_maker(photo_reference)

        global password_key
        user = user_id
        # password = password_key
        password = login_session['password']

        print('======Loading Existing Buildings======')
        response = get_response(user, password)
        buildings = response['Item']['buildings']
        print('======Generating New Building Info======')
        print(location)
        new_building = {
            name: {
                'location': make_dynamo_JSON(location['lat'], location['lng']),
                'address_street': address[0],
                'address_city': address[1],
                'address_postal': address[2],
                'rating': str(rating),
                'photo_reference': full_reference
            }
        }

        # Add new building to existing building list
        buildings.update(new_building)
        print('======Updating Dynamodb======')
        # Update building list on Dynamodb
        update_info(user, password, buildings)
        print('======Finishing======')
        return redirect(url_for('userRestaurant', user_id=user_id))
    else:
        return render_template('newBuilding.html', user_id=user_id)


@app.route('/restaurant/<string:user_id>/<string:title>/<string:address>event', methods=['GET', 'POST'])
def check_dashboard(user_id, title, address):
    print(title)
    if 'username' not in login_session:
        return redirect('/login')

    if login_session['user_id'] != user_id:
        return render_template('showwarning.html', user_id=login_session['user_id'])

    response = get_event_response(title, address)

    # Building event not found
    if 'Item' not in response:
        result = []
        return render_template('buildingEvents.html', user_id=login_session['user_id'], result=result,
                               message='No Event Yet, Make one NOW!', title=title, address=address)
    # Building event found (but could be empty)
    else:
        events = response['Item']['events']
        result = get_event_info(events)
        if not result:
            return render_template('buildingEvents.html', user_id=login_session['user_id'], result=result,
                                   message='No Event Yet, Make one NOW!', title=title, address=address)
        else:
            return render_template('buildingEvents.html', user_id=login_session['user_id'], result=result,
                                   message='Events Created by Others', title=title, address=address)


@app.route('/restaurant/<string:user_id>/<string:title>/<string:address>event/new', methods=['GET', 'POST'])
def newEvent(user_id, title, address):
    print('====='+title)
    return render_template("event.html", restaurant=title, address=address, user_id=user_id)


@app.route('/restaurant/<string:user_id>/<string:title>/<string:address>event/submit', methods=['GET', 'POST'])
def event_submit(user_id, title, address):
    time = str(request.form['time'])
    party_size = str(request.form['party_size'])
    description = str(request.form['description'])
    if time == "" or party_size == "":
        flash("Time and Party Size cannot be empty")
        return render_template("event.html", restaurant=title, address=address, user_id=user_id)

    if description == "":
        description = "None"

    if not party_size.isdigit():
        flash("Party Size has to be integer!")
        return render_template("event.html", restaurant=title, address=address, user_id=user_id)

    # convert time format
    full_time = str(dateutil.parser.parse(time))
    date = full_time.split()[0]
    time = full_time.split()[1]
    date_array = date.split('-')
    year = date_array[0]
    month = date_array[1]
    char_month = month_char(month)
    day = date_array[2]
    print('========time is: ' + time + ' year: ' + year + ' month: ' + month + ' day: ' + day)
    # Add host event to User database
    user = user_id
    password = login_session['password']
    response = get_response(user, password)
    firstname = response['Item']['firstname']
    lastname = response['Item']['lastname']
    full_name = firstname + ' ' + lastname
    age = response['Item']['age']
    gender = response['Item']['gender']
    email = response['Item']['email']
    host_event = response['Item']['host']
    new_host = {
        'title': title,
        'address': address,
        'year': year,
        'month': month,
        'char_month': char_month,
        'day': day,
        'time': time,
        'full_time': full_time,
        'party_size': party_size,
        'description': description
    }
    host_event.append(dict(new_host))
    update_host_info(user_id, password, host_event)
    # Add host event to Event database so other can see
    new_event = {
        'username': user_id,
        'full_name': full_name,
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
    response = get_event_response(title, address)
    if 'Item' not in response:
        table = dynamodb.Table('Events')
        response = table.put_item(
            Item={
                'building_name': title,
                'building_address': address,
                'events': [
                    new_event
                ]
            }
        )

    else:
        events = response['Item']['events']
        events.append(dict(new_event))
        response = update_event_info(title, address, events)

    return redirect(url_for('userRestaurant', user_id=user_id))


@app.route('/restaurant/<string:user_id>/<string:title>/<string:address>/<string:event>join', methods=['GET', 'POST'])
def join_event(user_id, title, address, event):
    event = literal_eval(event)
    print(event)
    # Add join event to User database
    user = user_id
    password = login_session['password']
    response = get_response(user, password)
    age = response['Item']['age']
    gender = response['Item']['gender']
    email = response['Item']['email']
    joining_event = response['Item']['joining']
    new_joining = {
        'title': title,
        'host': event['full_name'],
        'email': event['email'],
        'address': address,
        'year': event['year'],
        'month': event['month'],
        'char_month': event['char_month'],
        'day': event['day'],
        'time': event['time'],
        'full_time': event['full_time'],
        'party_size': event['party_size'],
        'description': event['description']
    }
    joining_event.append(dict(new_joining))
    update_joining_info(user_id, password, joining_event)

    return redirect(url_for('userRestaurant', user_id=user_id))


@app.route('/restaurant/<string:user_id>/<string:title>/delete', methods=['GET', 'POST'])
def deleteRestaurant(user_id, title):
    if 'username' not in login_session:
        return redirect('/login')

    if login_session['user_id'] != user_id:
        return render_template('showwarning.html', user_id=login_session['user_id'])

    if request.method == 'POST':
        # session.delete(itemToDelete)
        # session.commit()
        global password_key
        user = user_id
        # password = password_key
        password = login_session['password']

        print('======Loading Existing Buildings======')
        response = get_response(user, password)
        buildings = response['Item']['buildings']

        # Delete target building from building list
        buildings.pop(title)

        # Update Dynamodb
        update_info(user, password, buildings)

        return redirect(url_for('userRestaurant', user_id=user_id))
    else:
        return render_template(
            'deleteBuilding.html', user_id=user_id, item=title)


@app.route('/restaurant/<string:user_id>/<string:title>/<string:address>/<string:time>delete_join', methods=['GET', 'POST'])
def delete_joined_event(user_id, title, address, time):
    print('caonimacaonima')
    print(time)
    # Check User DB
    user = user_id
    password = login_session['password']
    response = get_response(user, password)
    joining_event = response['Item']['joining']
    print(joining_event)
    print('=======')
    for each_join in joining_event:
        if each_join['title'] == title and each_join['full_time'] == time and each_join['address'] == address:
            print(each_join)
            print('=======')
            # Delete target event
            index = joining_event.index(each_join)
            del joining_event[index]
            print('===============Join Event Removed=================')

    # Update DB
    update_joining_info(user_id, password, joining_event)
    return redirect(url_for('userRestaurant', user_id=user_id))


@app.route('/restaurant/<string:user_id>/<string:title>/<string:address>/<string:time>delete_host', methods=['GET', 'POST'])
def delete_host_event(user_id, title, address, time):
    user = user_id
    password = login_session['password']
    response = get_response(user, password)
    host_event = response['Item']['host']
    for each_host in host_event:
        if each_host['title'] == title and each_host['full_time'] == time and each_host['address'] == address:
            print(each_host)
            print('=======')
            index = host_event.index(each_host)
            del host_event[index]
            print('===============Host Event Removed from user db=================')

    # Update DB
    update_host_info(user_id, password, host_event)

    # Delete event from Events table
    response = get_event_response(title, address)
    event_list = response['Item']['events']
    for each_event in event_list:
        if each_event['username'] == user_id and each_event['full_time'] == time:
            index = event_list.index(each_event)
            del event_list[index]
            print('===============Host Event Removed from event db=================')

    # Update Event DB
    update_event_info(title, address, event_list)
    return redirect(url_for('userRestaurant', user_id=user_id))

# ===============Dynamodb Functions===============
# Create building table for application
# Do nothing if table already exist
def create_table():
    try:
        table = dynamodb.create_table(
            TableName='Buildings',
            KeySchema=[
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'password',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'username',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'password',
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


# Delete table
def delete_table():
    # dynamodb = boto3.client('dynamodb', region_name='us-east-1', endpoint_url="http://localhost:8000")
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    response = dynamodb.delete_table(
        TableName='Buildings'
    )
    response = dynamodb.delete_table(
        TableName='Events'
    )


# Get User Item from Dynamodb
def get_response(username, password):
    # Get username from dynamodb
    table = dynamodb.Table('Buildings')
    username = username
    password = password
    response = table.get_item(
        Key={
            'username': username,
            'password': password
        }
    )
    return response


# Update User Item in Dynamodb
def update_info(username, password, building_json):
    table = dynamodb.Table('Buildings')
    username = username
    password = password
    response = table.update_item(
        Key={
            'username': username,
            'password': password
        },
        UpdateExpression="set buildings = :b",
        ExpressionAttributeValues={
            ':b': building_json
        }
    )


# ===============Helper Functions===============
def hashed(keyword):
    salt = "1Ha7"
    hash = hashlib.md5((salt + keyword).encode('utf-8')).hexdigest()
    return hash


# Create JSON ready for Google
def make_json(lat, lon):
    lat = float(lat)
    lon = float(lon)
    geo_json = {
        'lat': lat,
        'lng': lon
    }
    print('Geo JSON created:')
    print(geo_json)
    return geo_json


# Create JSON ready for Dynamodb
def make_dynamo_JSON(lat, lng):
    lat = str(lat)
    lon = str(lng)
    dynamo_json = {
        'lat': lat,
        'lon': lon
    }
    print('Dynamodb JSON created:')
    print(dynamo_json)
    return dynamo_json


# Serialize Data
def serialize_data(title, location_json, street, city, postal, rating, photo_reference):
    return {
        'title': title,
        'location': location_json,
        'address_street': street,
        'address_city': city,
        'address_postal': postal,
        'rating': rating,
        'photo_reference': photo_reference
    }


# Get Building Info Ready to Display
def get_building_info(buildings):
    print(buildings)
    print('===========Loading Buildings===========')
    result_array = []
    if not buildings:
        print('===========Building List Empty===========')
        return result_array

    else:
        for building in buildings:
            title = building
            location_json = make_json(buildings[building]['location']['lat'], buildings[building]['location']['lon'])
            street = buildings[building]['address_street']
            city = buildings[building]['address_city']
            postal = buildings[building]['address_postal']
            rating = buildings[building]['rating']
            photo_reference = buildings[building]['photo_reference']
            result_array.append(serialize_data(title, location_json, street, city, postal, rating, photo_reference))
        print('===========Finished Loading===========')
        print(result_array)
        return result_array


def photo_reference_maker(photo_reference):
    if photo_reference == 'Not Found':
        return url_for('static/img', filename='download.png')
    head = 'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference='
    tail = '&key=your key'
    return head+photo_reference+tail


def time_split(time):
    date_time = time.split('T')
    print(date_time)
    return date_time


def month_char(month):
    month_array = ['None', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return month_array[int(month)]


if __name__ == "__main__":
    app.run(debug=True, host='localhost', port=4000)
