import json
import os

import mysql.connector


BASEDIR = os.path.dirname(os.path.abspath(__file__))


class Database:

    def __init__(self, creds):
        self._con = None
        self._creds = creds

    def connect(self):
        self._con = mysql.connector.connect(**self._creds)

    def send_data(self, data, table='Sample'):
        if self._con is None:
            print('Not connected!')
            return

        cursor = self._con.cursor()
        cursor.execute('INSERT INTO ' + table +
                       ' (date, temperature, pressure, humidity) '
                       'VALUES (%s, %s, %s, %s)',
                        data)
        self._con.commit()

        if cursor.rowcount == 1:
            print(f'Insertion to database {self._creds["database"]} '
                  f'at {self._creds["host"]} successful')
        else:
            print('Failed to insert data to database! No rows changed.')

    def disconnect(self):
        if self._con is not None:
            self._con.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()


if __name__ == '__main__':
    BASEDIR = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(BASEDIR, 'credentials.json')) as f:
        settings = json.load(f)

    with Database(settings['database']) as db:
        db.send_data(('2018-02-03', '14:00', 23, 99, 99))