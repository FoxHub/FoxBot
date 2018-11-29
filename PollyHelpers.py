# A helper file adopted based on:
#   1. https://medium.com/@julsimon/amazon-polly-hello-world-literally-812de2c620f4
#   2. https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

import boto3

defaultRegion = 'us-east-1'
defaultUrl = 'https://polly.us-east-1.amazonaws.com'
audioFormat = 'mp3'
pollyVoice = 'Salli'


def connectToPolly(regionName=defaultRegion, endpointUrl=defaultUrl):
    return boto3.client('polly', region_name=regionName, endpoint_url=endpointUrl)


def tts(text, location, format=audioFormat, voice=pollyVoice):
    polly = connectToPolly()
    resp = polly.synthesize_speech(OutputFormat=format, Text=text, VoiceId=voice)
    audiofile = open(location, 'wb')
    soundBytes = resp['AudioStream'].read()
    audiofile.write(soundBytes)
    audiofile.close()