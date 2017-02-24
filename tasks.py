from textwrap import dedent

import requests
from invoke import task
from configparser import ConfigParser

from handler.message_handler import MessageHandler

config = ConfigParser()
config.read('private.cfg')


@task
def deploy(ctx):
    ctx.run("lambda-uploader")


@task
def set_webhook(ctx):
    r = requests.post('https://api.telegram.org/bot{}/setWebhook'.format(config.get('main', 'bot_token')),
                      data={'url': config.get('main', 'lambda_api_url')})
    print(r.text)


@task
def print_commands(ctx):
    commands = [(cmd, dedent(f.__doc__ or '').strip())
                for cmd, f in MessageHandler.__dict__.iteritems()
                if cmd[0:5] == '_cmd_']

    for cmd, desc in commands:
        if desc:
            print('{} - {}'.format(cmd.split('_cmd_')[1], desc))
