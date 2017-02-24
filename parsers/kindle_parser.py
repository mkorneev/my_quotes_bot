# coding=utf-8

"""
Parser for Kindle clippings file
"""

import codecs
from collections import namedtuple

Quote = namedtuple('Quote', 'text')


def parse(path):
    """
    Returns generator which yields Quotes
    """
    with codecs.open(path, 'r') as f:
        while f.readline():
            f.readline()
            f.readline()
            line4 = f.readline()
            f.readline()

            # title, author = re.findall(r'^(.*) \((.*)\)$', line1)[0]

            yield Quote(text=line4.strip().decode('utf-8'))
