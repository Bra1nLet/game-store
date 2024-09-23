# -*- coding: utf-8 -*-
# !usr/bin/env python
import itertools

import requests


def get_course(value_from, value_to='RUB'):
    r = requests.get(f'https://min-api.cryptocompare.com/data/price?fsym={value_from}&tsyms={value_to}')
    return r.json()[value_to]
