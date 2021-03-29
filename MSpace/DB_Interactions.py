import psycopg2
import datetime
from MSpace import Globals
import json

from MSpace.system_info import DATABASE_CREDENTIALS


def update_overview():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    sql = f'''SELECT * FROM private.inventory_overview WHERE date = %s;'''
    params = (monday,)

    output = select(sql, params)

    return output


def delete(query, params):
    """ delete part by part id """
    connection = None
    rows_deleted = 0
    try:
        # DATABASE_CREDENTIALS is import at the beginning of the script from system_info module
        connection = psycopg2.connect(user=DATABASE_CREDENTIALS['user'],
                                      password=DATABASE_CREDENTIALS['password'],
                                      host=DATABASE_CREDENTIALS['host'],
                                      port=DATABASE_CREDENTIALS['port'],
                                      database=DATABASE_CREDENTIALS['database'])
        # create a new cursor
        cur = connection.cursor()
        # execute the UPDATE  statement
        cur.execute(query, params)
        # get the number of updated rows
        rows_deleted = cur.rowcount
        # Commit the changes to the database
        connection.commit()
        # Close communication with the PostgreSQL database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()

    return rows_deleted


def insert(query, params):
    connection = None
    cursor = None

    try:
        # DATABASE_CREDENTIALS is import at the beginning of the script from system_info module
        connection = psycopg2.connect(user=DATABASE_CREDENTIALS['user'],
                                      password=DATABASE_CREDENTIALS['password'],
                                      host=DATABASE_CREDENTIALS['host'],
                                      port=DATABASE_CREDENTIALS['port'],
                                      database=DATABASE_CREDENTIALS['database'])

        cursor = connection.cursor()
        # print(cursor.mogrify(query, params))
        cursor.execute(query, params)
        # print if needed
        # print(connection.get_dsn_parameters(),"\n")

        connection.commit()
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        raise error

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")


def select(sql, params):
    results = None
    connection = None
    cursor = None

    try:
        # DATABASE_CREDENTIALS is import at the beginning of the script from system_info module
        connection = psycopg2.connect(user=DATABASE_CREDENTIALS['user'],
                                      password=DATABASE_CREDENTIALS['password'],
                                      host=DATABASE_CREDENTIALS['host'],
                                      port=DATABASE_CREDENTIALS['port'],
                                      database=DATABASE_CREDENTIALS['database'])

        cursor = connection.cursor()
        # print(cursor.mogrify(sql, params))
        query = cursor.mogrify(sql, params)
        cursor.execute(query)

        results = cursor.fetchall()
        connection.commit()

    except (Exception, psycopg2.Error) as error:
        print("Error fetching data from PostgreSQL table", error)

    finally:
        # closing database connection
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed \n")

            return results


def get_updated_part_values(group, key):
    query = '''SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s '''
    output = select(query, params=[('general_inventory',)])
    query = ("SELECT * FROM public.general_inventory WHERE "
             "(general_inventory.group_serial = %s AND part_id = %s)")
    params = [Globals.groups[group], key]

    info_out = select(query, params)

    Globals.inventory_entries_cols = []
    Globals.inventory_entries_vals = []

    for o in output:
        Globals.inventory_entries_cols.append(o[0])
    for e in range(len(info_out[0])):
        Globals.inventory_entries_vals.append(info_out[0][e])

    a_file = open("ResourceDir/variable_state.json", "r")
    Globals.inventory_lastused_namekey = json.load(a_file)
    a_file.close()

    Globals.inventory_lastused_namekey["l_open_var_inventory"]['group'] = group
    Globals.inventory_lastused_namekey["l_open_var_inventory"]['key'] = key

    a_file = open("ResourceDir/variable_state.json", "w")
    json.dump(Globals.inventory_lastused_namekey, a_file)
    a_file.close()


''' Add the following lines for logging
def insert(query, params):
    import logging
    import psycopg2
    from psycopg2.extras import LoggingConnection

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    connection = None
    cursor = None

    try:
        # DATABASE_CREDENTIALS is import at the beginning of the script from system_info module
        connection = psycopg2.connect(user=DATABASE_CREDENTIALS['user'],
                                      password=DATABASE_CREDENTIALS['password'],
                                      host=DATABASE_CREDENTIALS['host'],
                                      port=DATABASE_CREDENTIALS['port'],
                                      database=DATABASE_CREDENTIALS['database'],
                                      connection_factory=LoggingConnection)
        connection.initialize(logger)

        cursor = connection.cursor()
        cursor.execute(query, params)
        # print if needed
        # print(connection.get_dsn_parameters(),"\n")

        connection.commit()
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
'''
