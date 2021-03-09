# Script that contains functions that format and return required date string
from datetime import date


def mdy():
    # mm/dd/YY
    today = date.today()
    d = today.strftime("%m%d%Y")

    return d


def ymd():
    # YYYY/mm/dd
    today = date.today()
    d = today.strftime("%Y/%m/%d")

    return d


def year():
    today = date.today()
    y = today.strftime("%Y")

    return int(y)