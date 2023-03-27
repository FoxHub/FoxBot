# A helper file adopted based on:
#   1. https://medium.com/@julsimon/amazon-polly-hello-world-literally-812de2c620f4
#   2. https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

import boto3

DEFAULT_REGION = 'us-west-2'
DEFAULT_URL = 'https://polly.us-west-2.amazonaws.com'
AUDIO_FORMAT = 'mp3'
POLLY_VOICE = 'Salli'


def _connect_to_polly(regionName=DEFAULT_REGION, endpointUrl=DEFAULT_URL):
    return boto3.client('polly', region_name=regionName, endpoint_url=endpointUrl)


def tts(text, file_location, format=AUDIO_FORMAT, voice=POLLY_VOICE):
    polly = _connect_to_polly()
    resp = polly.synthesize_speech(OutputFormat=format, Text=text, VoiceId=voice)
    audiofile = open(file_location, 'wb')
    sound_bytes = resp['AudioStream'].read()
    audiofile.write(sound_bytes)
    audiofile.close()
