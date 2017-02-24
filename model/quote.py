#!/usr/bin/env python
from model.db import DB


class Quote(DB):
    QUOTE_ID_FORMAT = '{}-{}'
    _table = DB.dynamodb.Table("MQB_Quotes")

    def __init__(self, quote_list_id, quote_number):
        DB.__init__(self)
        self._id = Quote.QUOTE_ID_FORMAT.format(quote_list_id, quote_number)
        self._number = quote_number

        item = Quote._table.get_item(
            Key={
                'quote_id': self._id,
            }
        ).get('Item')

        self._text = item['text']

    @property
    def text(self):
        return self._text

    @property
    def number(self):
        return self._number

    @staticmethod
    def create(quote_list_id, quote_number, text):
        Quote._table.put_item(
            Item={
                'quote_id': Quote.QUOTE_ID_FORMAT.format(quote_list_id, quote_number),
                'quote_list_id': quote_list_id,
                'text': text
            }
        )