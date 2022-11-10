import datetime
import ipaddress
import json
import pika
import os
import logging
from dotenv import load_dotenv
from flask import Flask, request

# Let's load some environment variables first

load_dotenv()

# some reusable functions for logging messages here...

def validation_failure_message(field):
    return f"\n{field} validation failed\n"


def validation_success_message(field):
    return f"\n{field} validation passed, proceeding..."

# configuring logging format

logging.basicConfig(format='\n%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S')

# setting a sublogger, since default root logger will show unnecesery logs from libraries

logger = logging.getLogger('web service')

# setting lowest logging level that is to be shown.

logger.setLevel(logging.INFO)

# Flask constructor

app = Flask(__name__)

# routing, we need to post this request since it's a payload

@app.route('/', methods=['POST'])

# Large view function, apperently Flask either only allows 1 function per route
# or it's implemented in a way that I do not know yet as a beginner, so I cant split this up.
# Maybe if I used Classes it would work? I don't know, but that would introduce more complexity that I dont need now.

def validate_JSON():

    # First, let's check if payload is at all a valid JSON format
    # This should fail if it's not JSON

    try:
        payload_contents = request.get_json()
        logger.info(validation_success_message("JSON"))
    except:
        logger.error(validation_failure_message("JSON"))
        return 'Not a valid JSON payload, check the payload and try again', 400

    # timestamp validation check

    try:

        # assigning timestamp to a variable here will check if "ts" field exists at all
        # since the value of ts is string, we also need to convert it into integer, hence the int conversion
        # you can also just pass "ts" value as a regular number instead of string and it will work too,
        # nothing was mentioned about this in validation rules so I left that possibilty in
        # otherwise I would check if the value is string beforehand and only then proceed with the rest of the validation

        payload_timestamp = int(payload_contents['ts'])

        # This will validate ts value and check if it's unix(epoch) timestamp(so no negative values, or invalid data types can be passed)
        # apperently .fromtimestamp() will allow values that correspond to year higher than 2038,
        # even though traditionally it's not supposed to since timestamps should be 32 bit value
        # according to this website: https://python.astrotech.io/intermediate/datetime/timestamp.html
        # on some systems you can have values here that are higher than 32 bit, so I added addition check
        # that will check if value does not exceed 32 bits, to comply with original specification.

        datetime.date.fromtimestamp(payload_timestamp)

        if payload_timestamp.bit_length() < 32:
            logger.info(validation_success_message("timestamp"))
        else:
            logger.error(validation_failure_message("timestamp"))
            return 'timestamp higher than unix time allows, please check ts key value and try again', 400
    except:
        logger.error(validation_failure_message("timestamp"))
        return 'ts field either missing or invalid format, please check keys and values and try again', 400

    # sender field validation
    # in validation rules it asks me that the sender must be a string
    # however, string data types can also technically be a number,
    # so if you put it in double quotes like this "20", it will still be
    # a string containing a number.
    # it's not clear whether I should accept such input or not.
    # So, I added check to see if the string contains only numbers or is a float,
    # Since I assume that sender field should be an actual text,
    # rather than just some sort of numeric id.
    # if my assumption is wrong then removing those couple of checks wont break anything.

    try:

        # this will fail if sender field is not present

        payload_sender = payload_contents['sender']

        # check if sender value is a string

        if isinstance(payload_sender, str) == True:

            # check if sender value is not empty

            if payload_sender != "":

                # check if sender value is not numeric

                if payload_sender.isnumeric() != True:

                    # check if sender value can be converted to float, else proceed

                    try:
                        float(payload_sender)
                        logger.error(validation_failure_message("sender"))
                        return 'sender has float as their value, enter valid sender name that is a string', 400
                    except:
                        logger.info(validation_success_message("sender"))
                else:
                    logger.error(validation_failure_message("sender"))
                    return 'your sender value is numeric, please enter valid sender name', 400
            else:
                logger.error(validation_failure_message("sender"))
                return 'sender key value is empty, please enter valid senders name', 400
        else:
            logger.error(validation_failure_message("sender"))
            return 'sender value must be a string! Check if your value is correct data type and try again', 400

    except:
        logger.error(validation_failure_message("sender"))
        return 'sender field either missing or invalid format, please check keys and values and try again', 400

    # message field validation

    try:

        # check if field exists

        payload_message = payload_contents['message']

        # since json objects are converted to dict in python
        # this will check if the data type is correct

        if isinstance(payload_message, dict) == True:

            # This will check if the message is empty and if it has
            # at least one key value pair set, aka at least one field.
            # It specifically checks if keys exist and if at least one of the keys is not empty(aka True).
            # The key values pairs can be anything you want and as many as you want
            # This is also where i found out about "any" function, I could probably rewrite
            # some earlier checks with this, but at this point I don't have time.

            if any(payload_message.values()):
                logger.info(validation_success_message("message"))
            else:
                logger.error(validation_failure_message("message"))
                return 'your message is empty or keys have no value, please check if you have at least 1 field set properly and try again', 400

        else:
            logger.error(validation_failure_message("message"))
            return 'message must be a valid nested json object, please check message data type', 400

    except:
        logger.error(validation_failure_message("message"))
        return 'message field either missing or invalid format, please check it and try again', 400

    # ipv4 field validation
    # I only check for ipv4 address, it should throw an error if you try to pass ipv6
    # local ip address allowed, since they do technically fit ipv4 spec

    try:

        # if the field does not exist it will just skip entire validation

        payload_ipv4 = payload_contents['sent-from-ip']

        # used ipaddress library, passing anything to IPv4Address that is not ipv4 should fail
        # trying to pass ipv4 address with subnet mask using slash notation like this "192.168.1.0/24" will fail too

        try:
            ipaddress.IPv4Address(payload_ipv4)
            logger.info(validation_success_message("ipv4"))
        except:
            logger.error(validation_failure_message("ipv4"))
            return 'your provided ip address is not valid format, check its values to make sure its ipv4 and try again', 400

    except:
        logger.warning("\nNo ipv4 provided, skipping... (OPTIONAL).")

    # field validation check, this will deny all fields that are not valid.
    # I think I implemented this quite wierdly, but it works by having base "template" of keys
    # in a set, that I check against payloads key set by using .issubset() function.
    # This will allow all keys that are the same as in "template", but nothing more.
    # However, it does not check if fields are missing, so it will allow sent-from-ip
    # and priority fields to be omitted, while the rest of the fields are required by
    # validations previously done, so they will be present.
    # I assume that priority field can be omitted, since nothing was said that it must be
    # present in validation rules

    valid_playload_keys = {'ts', 'sender',
                           'message', 'sent-from-ip', 'priority'}

    if set(payload_contents).issubset(valid_playload_keys):
        logger.info(validation_success_message("invalid field"))
        logger.info("\npayload is now being passed into queue")

        # Establishing queue connection
        # Passing username, password and host as an enviromental variable since
        # these need to be changed depending if you are running locally or on Docker/K8.

        username_credentials_env = os.getenv('AMQP_USER')
        password_credentials_env = os.getenv('AMQP_PASS')
        host_env = os.getenv('AMQP_HOST')
        credentials = pika.PlainCredentials(
            username_credentials_env, password_credentials_env)
        parameters = pika.ConnectionParameters(
            host_env, 5672, '/', credentials)

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Declaring queue name

        channel.queue_declare(queue='payload_queue_1')

        # Passing payload contents to the queue

        channel.basic_publish(
            exchange='', routing_key='payload_queue_1', body=json.dumps(payload_contents))

        # closing connection
        
        connection.close()
        
        # this will be returned if all validations inside validate_JSON() function will pass sucessfully

        return 'validation passed, sending payload into queue', 200
    else:
        logger.error(validation_failure_message("invalid field"))
        return 'you entered field that is not valid, please remove it and try again', 400


if __name__ == "__main__":
    app.run()
