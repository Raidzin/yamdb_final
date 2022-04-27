import sqlite3
import os
import csv

INSERT = "INSERT INTO {0} ({1}) VALUES ({2});"


def get_columns_and_values(row):
    into = list(row.keys())
    values = list(row.values())
    for i, value in enumerate(values):
        value = value.replace("'", "''")
        values[i] = f"'{value}'"
    return into, values


def add_user_system_data(into, values):
    into.extend(('password', 'is_superuser',
                 'is_staff', 'is_active', 'date_joined'))
    values.extend(('0', '0', '0', '0', '0'))
    return into, values


def write_data(cur, table_name, into, values):
    cur.execute(
        INSERT.format(
            table_name,
            ', '.join(into),
            ', '.join(values)
        )
    )


def parse_csvs(file_names, cur):
    for file_name in file_names:
        table_name = 'reviews_' + file_name[:-4]
        with open(file_name, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                into, values = get_columns_and_values(row)
                if table_name == 'reviews_user':
                    into, values = add_user_system_data(into, values)
                write_data(cur, table_name, into, values)
    cur.execute('COMMIT;')


if __name__ == '__main__':
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()

    os.chdir('static')
    os.chdir('data')

    file_names = [file for file in os.listdir() if file.endswith('.csv')]

    parse_csvs(file_names, cur)
