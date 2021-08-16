#!/usr/bin/env python

from datetime import datetime
import json
import os
import sys

# RPI
import board
import time
from smbus import SMBus
import RPi.GPIO as GPIO

# Sensors
import adafruit_dht
from bmp280 import BMP280

# Local
from db import Database
from mail import MailHandler

# Sensor params
MAX_DHT_ATTEMPTS = 100
BMP280_I2C_ADDR = 0x77
LED_PIN = 17    # BCM

BASEDIR = os.path.dirname(os.path.abspath(__file__))


def init_led():
    """ Initialize LED to show that we're taking a sample. """
    GPIO.setup(LED_PIN, GPIO.OUT)
    pwm = GPIO.PWM(LED_PIN, 60)
    pwm.start(35)
    return pwm


if __name__ == '__main__':
    pwm = init_led()
    print('Taking sample...')

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

    import time

    # The DHT11 sensor is very time-sensitive and sometimes
    # the rpi isn't fast enough and need several attempts.
    attempts = 0
    measure_ok = False
    while attempts < MAX_DHT_ATTEMPTS and not measure_ok:
        try:
            dht.measure()
            temp1 = dht.temperature
            humidity = dht.humidity
            measure_ok = True

        # Measurements require 2 seconds between readings.
        # Having a shorter delay will fail!
        except RuntimeError:
            time.sleep(2)

        attempts += 1

    print(f'DHT reading took {attempts} attempts')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Read data from BMP
    temp2 = bmp280.get_temperature()
    pressure = bmp280.get_pressure()

    # If DHT still failed, we ignore that value this time.
    if temp1 is None:
        mailhandler.send(f'Failed to read DHT sensor {timestamp}')
        temperature = round(temp2, 2)
    else:
        temperature = round((temp1 + temp2) / 2, 2)

    pressure = int(round(pressure, 0))
    print(f'Temperature: {temperature} C, Humidity: {humidity}'
          f' Pressure: {pressure}')

    # Prepare data for database insertion
    data = (timestamp, temperature, pressure, humidity)

    try:
        with Database(settings['database']) as db:
            print(f'Saving {data} to database')
            db.send_data(data)
    except Exception as e:
        mailhandler.send(f'Error occured at {timestamp}:\n{str(e)}')

    # Take an image
    try:
        img_settings = settings['image']

        date, time_ = timestamp.split(' ')
        time_ = time_[:-3]   # Don't need seconds.

        # Images are organized in folders for each date.
        dir_name = os.path.join(img_settings['output'], date)
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

        # Name of image is date and time
        img_name = f'{date.replace(":", "-")}_{time_.replace(":", "-")}.jpg'

        # Image location is IMAGES/CURRENT_DATE/IMG.jpg
        img_output = os.path.join(dir_name, img_name)

        # Remote target is location on remote machine.
        remote_dir = os.path.join(img_settings['remote_location'], date)
        remote_img = os.path.join(remote_dir, img_name)

        import subprocess

        print('Taking image...')
        subprocess.run(['raspistill', '-q', str(img_settings['quality']), '-vf', '-hf',  '-o', img_output])
        try:
            # Ensure that dir exists on remote machine
            remote_host = img_settings['remote_host']
            subprocess.run(['ssh', remote_host, '"mkdir"',
                            '"-p"', f'"{remote_dir}"'])

            print('Image taken, sending to remote host through scp...')
            # Copy the image to remote machine.
            subprocess.run(['scp', img_output, f'{remote_host}:{remote_dir}'])
        except Exception as e:
            print(f'Error using scp: \n{str(e)}')
            mailhandler.send(f'Error using scp: \n{str(e)}')


    except Exception as e:
        print(f'Unknown exception: {e}')
        mailhandler.send(f'Error occured when taking image {timestamp}:\n{str(e)}')
    finally:
        pwm.stop()

        # Need to clean up and release channels
        GPIO.cleanup()

        print('Done, cleaning up! ')
