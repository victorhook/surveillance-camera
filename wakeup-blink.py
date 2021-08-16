#!/usr/bin/env/python3

import RPi.GPIO as GPIO
import time

LED_PIN = 17    # BCM
pwm = None
BLINK_DELAY = .5     # In seconds.


def blink():
    pwm.start(35)
    time.sleep(BLINK_DELAY)
    pwm.stop()
    time.sleep(BLINK_DELAY)


if __name__ == '__main__':
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LED_PIN, GPIO.OUT)
        pwm = GPIO.PWM(LED_PIN, 60)

        for i in range(5):
            blink()

    except Exception as e:
        print(f'Unknown error: {e}')
    finally:
        GPIO.cleanup()