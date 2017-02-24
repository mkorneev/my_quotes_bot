#!/usr/bin/env python
from __future__ import print_function

import os
import sys
from configparser import ConfigParser
import json
import logging
import telepot
import time

from handler.message_handler import MessageHandler

"""
$ python2.7 telegram my_quotes_bot AWS lambda handler
"""

logger = logging.getLogger()
logging.basicConfig()
logger.setLevel(logging.WARN)

config = ConfigParser()
config.read('private.cfg')

bot = telepot.Bot(config.get('main', 'bot_token'))
debug_chat_id = config.getint('main', 'debug_chat_id')

mh = MessageHandler(bot)


def handle_message(msg):
    try:
        flavor = telepot.flavor(msg)

        # normal message
        if flavor == 'chat':
            # content_type, chat_type, chat_id = telepot.glance(msg)
            # print('Normal Message:', content_type, chat_type, chat_id)
            mh.handle_chat_message(msg)
    except Exception as e:
        text = '{}: {}, {}, {}'.format(
            sys.exc_info()[0].__name__,
            e.message,
            os.path.basename(sys.exc_info()[2].tb_frame.f_code.co_filename),
            sys.exc_info()[2].tb_lineno
        )

        logger.exception(text)
        send_debug_message(text)

    # # inline query - need `/setinline`
    # elif flavor == 'inline_query':
    #     query_id, from_id, query_string = telepot.glance(msg, flavor=flavor)
    #     print('Inline Query:', query_id, from_id, query_string)
    #
    #     # Compose your own answers
    #     articles = [{'type': 'article',
    #                  'id': 'abc', 'title': 'ABC', 'message_text': 'Good morning'}]
    #
    #     bot.answerInlineQuery(query_id, articles)
    #
    # # chosen inline result - need `/setinlinefeedback`
    # elif flavor == 'chosen_inline_result':
    #     result_id, from_id, query_string = telepot.glance(msg, flavor=flavor)
    #     print('Chosen Inline Result:', result_id, from_id, query_string)
    #
    #     # Remember the chosen answer to do better next time
    #
    # else:
    #     print('Flavor:', flavor)
    #     raise telepot.exception.BadFlavor(msg)


def send_debug_message(text):
    bot.sendMessage(debug_chat_id, text)


def my_handler(event, context):
    logger.debug("Received event: " + json.dumps(event, indent=2))

    if "message" in event:
        handle_message(event['message'])
    elif "source" in event and event["source"] == "aws.events":
        mh.send_scheduled_quotes()


if __name__ == '__main__':
    bot.setWebhook()
    bot.message_loop(handle_message)
    print('I am listening ...')

    while 1:
        time.sleep(10)
