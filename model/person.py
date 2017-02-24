#!/usr/bin/env python
from model.db import DB
from model.quote_list import QuoteList


class Person(DB):
    _table = DB.dynamodb.Table("MQB_Persons")

    def __init__(self, value):
        DB.__init__(self)

        if isinstance(value, int):
            self._id = value
        else:
            self._id = value['PersonID']
            self._map = value

        self._quote_lists = None

    @property
    def id(self):
        return self._id

    @property
    def map(self):
        if not self._map:
            self._map = Person._table.get_item(
                Key={
                    'PersonID': self.id,
                }
            ).get('Item')

        return self._map

    @property
    def settings(self):
        return self.map['settings']

    @property
    def quote_lists(self):
        if self._quote_lists is None:
            self._quote_lists = [QuoteList(q) for q in self._map['quote_lists']]
        return self._quote_lists

    @staticmethod
    def find(person_id):
        return Person(person_id)

    @staticmethod
    def find_all():
        people = Person._table.scan(
            ProjectionExpression="PersonID, settings.send_at, quote_lists, last_sent_time",
        )

        return [Person(person) for person in people['Items']]

    @staticmethod
    def find_or_create(person_id):
        person = Person.find(person_id)
        if not person:
            value = {
                'settings': {}
            }
            Person._table.put_item(
                Item={
                        'PersonID': person_id
                     }.update(value)
            )
            person = Person(person_id)
        return person

    def update_sent_time(self, quote_list_id, time_):
        Person._table.update_item(
            Key={
                'PersonID': self.id
            },
            UpdateExpression='SET last_sent_time = if_not_exists(last_sent_time, :empty_map)',
            ExpressionAttributeValues={
                ':empty_map': {},
            }
        )

        Person._table.update_item(
            Key={
                'PersonID': self.id
            },
            UpdateExpression='SET last_sent_time.#k = :t',
            ExpressionAttributeNames={
                '#k': quote_list_id,
            },
            ExpressionAttributeValues={
                ':t': time_
            }
        )

    def last_sent_time_for(self, quote_list):
        return self._map.get('last_sent_time', {}).get(quote_list.id)

    def set_send_time(self, time_):
        Person._table.update_item(
            Key={
                'PersonID': self.id
            },
            UpdateExpression='SET settings.send_at = :t',
            ExpressionAttributeValues={
                ':t': time_
            }
        )

    def add_quote_list(self, quote_list):
        Person._table.update_item(
            Key={
                'PersonID': self.id
            },
            UpdateExpression='SET quote_lists = list_append(if_not_exists(quote_lists, :empty_list), :list)',
            ExpressionAttributeValues={
                ':list': [quote_list.id],
                ':empty_list': []
            },
            ReturnValues="UPDATED_NEW"
        )