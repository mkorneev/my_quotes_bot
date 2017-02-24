from __future__ import print_function

import logging
import pprint
import re
import time
from collections import namedtuple
from datetime import datetime
from textwrap import dedent

from model.db import DB
from model.person import Person
from model.quote_list import QuoteList
from parsers import kindle_parser

Message = namedtuple('Message', 'chat person command args')
pp = pprint.PrettyPrinter(indent=4)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _extract_command(text):
    """
    >>> _extract_command('/start')
    ('start', None)
    >>> _extract_command('/send_at 12:00 3')
    ('send_at', '12:00 3')
    """
    m = re.match(r'^/([^ ]+)( (.+))?', text)
    if not m:
        raise Exception("Cannot parse command %r" % text)
    return m.group(1), m.group(3)


class MessageHandler:
    def __init__(self, bot_):
        self.bot = bot_
        self.db = DB()

    def handle_chat_message(self, msg):
        self.db.store_message(msg)

        command, args = _extract_command(msg['text'])
        message = Message(chat=msg['chat']['id'],
                          person=msg['from']['id'],
                          command=command,
                          args=args)

        self._dispatch(message)

    def _dispatch(self, message):
        method_name = '_cmd_' + str(message.command)
        try:
            method = getattr(self, method_name)
        except AttributeError:
            self._send_reply(message, "Sorry, I didn't understand that command.")
        else:
            method(message)

    def _send_reply(self, message_or_chat, text):
        if isinstance(message_or_chat, Message):
            chat_id = message_or_chat.chat
        else:
            chat_id = message_or_chat

        msg = self.bot.sendMessage(chat_id, text)
        self.db.store_message(msg)

    def _cmd_start(self, message):
        Person.find_or_create(message.person)
        self._send_reply(message, 'Hi! I am My Quotes Telegram Bot!')

    def _cmd_help(self, message):
        self._send_reply(message,
                         dedent('''
                            They call me a Telegram Bot. I can help you do stuff.
                        '''))

    def _cmd_settings(self, message):
        person = Person.find_or_create(message.person)
        self._send_reply(message, person.settings)

    def _cmd_send_at(self, message):
        time_ = message.args
        Person.find(message.person).set_send_time(time_)

        if time_:
            self._send_reply(message, 'Scheduled sending random quotes at {} UTC'.format(time_))
        else:
            self._send_reply(message, 'Cleared scheduled sending of random quotes.')

    def _cmd_load_quotes(self, message):
        quotes_generator = kindle_parser.parse('C:\max\Projects\my_quotes_bot\data\My_Clippings.txt')

        quote_list_number = message.args

        if not quote_list_number:
            quote_list = QuoteList()
        else:
            raise NotImplemented()

        self._send_reply(message, "Loading new quotes")

        Person.find(message.person).add_quote_list(quote_list)
        count = quote_list.add_quotes(quotes_generator)

        self._send_reply(message, "Loaded {} quotes".format(count))

    def _cmd_count_quotes(self, message):
        if not message.args:
            raise Exception("List number should be specified")

        quote_list_number = int(message.args)
        quote_list = Person.find(message.person).quote_lists[int(quote_list_number)]

        self._send_reply(message, "This list has {} quotes".format(quote_list.size))

    def _cmd_show_quote(self, message):
        """
        /show_quote L N   Show quote N from list L
        """
        quote_list_number, quote_number = re.findall('^(\d+) (\d+)$', message.args)[0]

        if not quote_number:
            raise Exception("List number and quote number should be specified")

        quote_list_number, quote_number = int(quote_list_number), int(quote_number)

        quote_list = Person.find(message.person).quote_lists[int(quote_list_number)]
        quote = quote_list.get_quote(quote_number)

        self._send_reply(message, quote.text)

    def _cmd_show_random_quote(self, message):
        """
        /show_random_quote L   Show a random quote from list L
        """

        quote_list_number = re.findall('^(\d+)$', message.args)[0]

        if not quote_list_number:
            raise Exception("List number should be specified")

        quote_list = Person.find(message.person).quote_lists[int(quote_list_number)]
        self.send_random_quote(message.chat, quote_list)

    def send_random_quote(self, person, quote_list):
        quote = quote_list.get_random_quote()
        self._send_reply(person.id, quote.text)
        logger.info('Sent quote {} from list {} to {}'.format(quote.number, quote_list.id, person.id))

    def _cmd_send_scheduled_quotes(self, message):
        count = self.send_scheduled_quotes()
        self._send_reply(message, '{} messages sent'.format(count))

    def send_scheduled_quotes(self):
        people = Person.find_all()

        count = 0
        for person in people:
            for quote_list in person.quote_lists:
                hour, minute = map(int, person.settings['send_at'].split(':'))
                scheduled_dt = datetime.now().replace(hour=hour, minute=minute)
                scheduled_time = int(time.mktime(scheduled_dt.timetuple()))

                now = int(time.mktime(datetime.now().timetuple()))

                last_sent_time = person.last_sent_time_for(quote_list)
                if scheduled_time > now:
                    continue

                if last_sent_time and scheduled_time < last_sent_time + 60:
                    continue

                try:
                    self.send_random_quote(person, quote_list)
                    self._update_last_sent_time(person, quote_list)
                    count += 1
                except ValueError:
                    pass  # no quote to send

        return count

    @staticmethod
    def _update_last_sent_time(person, quote_list):
        now = int(time.mktime(datetime.now().timetuple()))
        person.update_sent_time(quote_list.id, now)
