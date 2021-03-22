#!/usr/bin/env python

from datetime import datetime
import json
import os
import sys

# RPI
import board
import time
from smbus import SMBus

# Sensors
import adafruit_dht
from bmp280 import BMP280

# Local
from db import Database
from mail import MailHandler
from cam import take_image

# Sensor params
MAX_DHT_ATTEMPTS = 10
BMP280_I2C_ADDR = 0x77


BASEDIR = os.path.dirname(os.path.abspath(__file__))


if __name__ == '__main__':
    try:
        with open(os.path.join(BASEDIR, 'credentials.json')) as f:
            settings = json.load(f)
    except FileNotFoundError as e:
        # Should not occur, somehting really bad have happened...
        print(f'Failed to open credentials... \n{str(e)}')
        sys.exit(0)


    mailhandler = MailHandler(settings['mail'])

    # Initialize the sensors
    dht = adafruit_dht.DHT11(board.D25)
    bmp280 = BMP280(i2c_addr=BMP280_I2C_ADDR, i2c_dev=SMBus(1))

    # The DHT11 sensor is very time-sensitive and sometimes
    # the rpi isn't fast enough and need several attempts.
    attempts = 0
    while attempts < MAX_DHT_ATTEMPTS:
        try:
            dht.measure()
            temp1 = dht.temperature
            humidity = dht.humidity
            attempts += 1

        except (RuntimeError, TypeError) as error:
            print(f'ERROR {attempts} DHT reading: {error}')

    date = str(datetime.now().date())
    time_ = datetime.now().time().strftime('%H:%M:%S')

    if temp1 is None:
        mailhandler.send(f'Failed to read DHT sensor {date} {time_}')

    # Read all the data
    temp2 = bmp280.get_temperature()
    pressure = bmp280.get_pressure()
    temperature = round((temp1 + temp2) / 2, 2)
    pressure = int(round(pressure, 0))

    print(f'T: {temperature}C, Hum: {humidity} Pres: {pressure}')

    # Prepare data for database insertion
    data = (date, time_, temperature, pressure, humidity)

    try:
        with Database(settings['database']) as db:
            print(f'Saving {data} to database')
            db.send_data(data)
    except Exception as e:
        mailhandler.send(f'Error occured at {date} {time}:\n{str(e)}')

    # Take an image
    remote = settings['image']['remote']
    img_quality = settings['image']['quality']
    img_name = f'{date.replace(":", "-")}_{time_.replace(":", "-")}.jpg'
    img_output = os.path.join(settings['image']['output'], img_name)
    remote_target = f'{remote}{img_name}'
    take_image(mailhandler, img_quality, img_output, remote_target)