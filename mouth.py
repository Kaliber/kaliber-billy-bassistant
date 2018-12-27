#!/usr/bin/env python

"""
animatronic_mouth.py

This script animates a motorized mouth on a Raspberry Pi GPIO pin so that it
appears to be speaking alongside the audio on the specified PulseAudio source
(which usually should be a sink's monitor).

Find PA_SOURCE with `pactl list` and look for a monitor device that corresponds
to your output device.

See here for a detailed discussion: https://albertarmea.com/post/alexa-tree/
"""

import atexit
import time
import struct
import subprocess
from adafruit_motorkit import MotorKit

def turnoffmotor():
  kit.motor1.throttle = 0

atexit.register(turnoffmotor)
kit = MotorKit()

PA_SOURCE = "alsa_output.usb-Generic_USB2.0_Device_20130100ph0-00.analog-stereo.monitor"
MOUTH_STATE = 'closed'
SAMPLE_ARRAY = []

# We're not playing this stream back anywhere, so to avoid using too much CPU
# time, use settings that are just high enough to detect when there is speech.
PA_CHANNELS = 1 # Mono
PA_RATE = 1000 # Hz
PA_LATENCY=4

SAMPLE_THRESHOLD = 2
COUNTER = 0

# Capture audio using `pacat` -- PyAudio looked like a cleaner choice but
# doesn't support capturing monitor devices, so it can't be used to capture
# system output.
parec = subprocess.Popen(["/usr/bin/pacat", "--record", "--device="+PA_SOURCE,
    "--rate="+str(PA_RATE), "--channels="+str(PA_CHANNELS),
    ], stdout=subprocess.PIPE)

while not parec.stdout.closed:
    # Mono audio with 1 byte per sample makes parsing trivial
    sample = ord(parec.stdout.read(1)) - 120
    COUNTER += 1
    SAMPLE_ARRAY.append(sample)

    if COUNTER % 50 == 0:
      sample_average = sum(SAMPLE_ARRAY, 0.0) / len(SAMPLE_ARRAY)
      #print(sample_average)

      if abs(sample_average) >= SAMPLE_THRESHOLD and MOUTH_STATE == 'closed':
        #print('open')
        kit.motor1.throttle = 1.0
        MOUTH_STATE = 'open'
      elif abs(sample_average) < SAMPLE_THRESHOLD and MOUTH_STATE == 'open':
        #print('close')
        kit.motor1.throttle = 0
        MOUTH_STATE = 'closed'

      SAMPLE_ARRAY = []
      COUNTER = 0