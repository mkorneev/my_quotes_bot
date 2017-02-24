#!/usr/bin/env python
import random
import uuid

from model.db import DB
from model.quote import Quote


class QuoteList(DB):
    _table = DB.dynamodb.Table("MQB_QuoteLists")

    def __init__(self, value=None):
        DB.__init__(self)

        if isinstance(value, int) or isinstance(value, basestring):
            self._id = value
        elif value is None:
            self._id = str(uuid.uuid4())
        else:
            raise NotImplementedError()

    @property
    def id(self):
        return self._id

    @property
    def size(self):
        return self.map['size']

    @property
    def map(self):
        if not self._map:
            self._map = QuoteList._table.get_item(
                Key={
                    'quote_list_id': self.id,
                }
            ).get('Item')

        return self._map

    def get_random_quote(self):
        self.get_quote(random.randrange(self.size))

    def get_quote(self, n):
        return Quote(self.id, n)

    def add_quotes(self, quotes):
        count = 0
        for quote in quotes:
            if quote.text:
                count += 1
                Quote.create(self.id, count, quote.text)

        QuoteList._table.put_item(
            Item={
                'quote_list_id': self.id,
                'size': count
            }
        )

        return count
