#!/usr/bin/env python

import boto3


class DB(object):
    dynamodb = boto3.resource('dynamodb')
    # dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
    messages_table = dynamodb.Table("MQB_Messages")

    def __init__(self):
        self._map = None

    @staticmethod
    def store_message(msg):
        DB.messages_table.put_item(
            Item={
                "ChatID": str(msg["chat"]["id"]),
                "MessageID": msg["message_id"],
                "PersonID": msg["from"]["id"],
                "Date": msg["date"],
                "Text": msg["text"]
            }
        )
