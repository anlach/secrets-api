# Secrets API

An fun, little encrypted message microservice. See it running here:
[https://g3y6mpvv9a.execute-api.us-west-2.amazonaws.com](https://g3y6mpvv9a.execute-api.us-west-2.amazonaws.com/)

## Front End

The front-end is HTML, CSS, and a tiny bit of JavaScript to enable a
message ID to be inserted into the URL of a POST request.

## Serverless Back End

The back-end is done with two Lambda functions written in Python 3.9. An
API Gateway creates the URL enpoints for the service. Only one endpoint,
for the `GET /all` route, is integrated with the "secrets-history"
lambda function. The rest are all kept in the "secrets" lambda function,
which does some routing itself in the top-level handler.

Most typical errors are handled and return a reasonable error message.

The `GET /` request returns the index.html text, and the `GET /style.css`
request returns the style.css text. This is how the front-end is served,
and it seems to work pretty well. Another page is served after a POST
request with details about how to read the message that was posted.

## Dynamo DB

A simple Dynamo DB table keeps track of the messages using the message IDs
as the partition keys. It might have been better to use some other partition
key, and to use a sort key for ordering within each partition. The original
design was to have a `GET /history` endpoint that only returned the last
10 messages, but since each message was in its own partition, scanning
the table can't really do this. Instead of re-designing the whole thing,
I just switched to using a `GET /all` endpoint that returns up to 100 messages,
which is probably more than there'll ever be.

## Encryption

GnuPG is used for symmetric encryption of the messages. This was found on 
the AWS Linux OS, but was unfortunately absent on the AWS Linux 2 that
came with Python 3.9.  For that reason, I stuck with the Python 3.7 execution
environment. I could probably figure out a way to install GPG in a layer.
Alternatively, the encryption ought to be doable with Python. There is
a cryptography package that could be installed, but it's probably not
as tried-and-true as simply using GPG as a subprocess. Probably better
would be the python-gnupg package.

