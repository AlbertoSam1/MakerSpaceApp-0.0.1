# In this script all types of generic ID will be created
import string
import random
from random import randint

from FormattedDate import mdy


# ID generator for Inventory Request ID
def get_inventory_rid():
    d = ""
    for i in range(4):
        d += str(random.choice(string.ascii_letters))
    d = d.upper()
    d += mdy()
    for e in range(2):
        d += str(randint(0, 9))

    return d


# Inventory group id
def get_inventory_gid():
    d = get_inventory_rid()[:4]

    for e in range(4):
        d += str(randint(0, 9))

    return d
