from DB_Interactions import select
from MSpace import Globals


def get_inventory_cols():
    query = '''SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s '''
    output = select(query, params=[('general_inventory',)])

    Globals.current_inventory_cols = []

    for o in output:
        Globals.current_inventory_cols.append(o[0])
