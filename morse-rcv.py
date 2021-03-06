#!/usr/bin/python

import pygame
import time
from RPi import GPIO
import thread
from array import array
from pygame.locals import *
from morse_lookup import *

pygame.mixer.pre_init(44100, -16, 1, 1024)
pygame.init()

class ToneSound(pygame.mixer.Sound):
    def __init__(self, frequency, volume):
        self.frequency = frequency
        pygame.mixer.Sound.__init__(self, self.build_samples())
        self.set_volume(volume)

    def build_samples(self):
        period = int(round(pygame.mixer.get_init()[0] / self.frequency))
        samples = array("h", [0] * period)
        amplitude = 2 ** (abs(pygame.mixer.get_init()[1]) - 1) - 1
        for time in xrange(period):
            if time < period / 2:
                samples[time] = amplitude
            else:
                samples[time] = -amplitude
        return samples

def wait_for_keydown(pin):
    while GPIO.input(pin):
        time.sleep(0.01)

def wait_for_keyup(pin):
    while not GPIO.input(pin):
        time.sleep(0.01)

def decoder_thread():
    global key_up_time
    global buffer
    new_word = False
    while True:
        time.sleep(.01)
        key_up_length = time.time() - key_up_time
        if len(buffer) > 0 and key_up_length >= 1.5:
            new_word = True
            bit_string = "".join(buffer)
            try_decode(bit_string)
            del buffer[:]
        elif new_word and key_up_length >= 4.5:
            new_word = False
            sys.stdout.write(" ")
            sys.stdout.flush()

tone_obj = ToneSound(frequency = 800, volume = .5)

pin = 7
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

DOT = "."
DASH = "-"
UNKNOWN = "?"

dot_max = 0.15
key_down_time = 0
key_down_length = 0
key_up_time = 0
buffer = []

if (len(sys.argv) > 1):
	dot_max = float(sys.argv[1])

dash_min     = 2.5 * dot_max 
letter_space = 2 * dot_max 
word_space   = 7 * dot_max

print( dot_max )
print( dash_min )
print( letter_space )
print( word_space )
print( "(WPM ~= 1 / dot_length)" )

thread.start_new_thread(decoder_thread, ())

print("Ready")

while True:
    wait_for_keydown(pin)
    key_down_time = time.time() #record the time when the key went down
    tone_obj.play(-1) #the -1 means to loop the sound
    wait_for_keyup(pin)
    key_up_time = time.time() #record the time when the key was released
    key_down_length = key_up_time - key_down_time  # how long it was down
    tone_obj.stop()
    if key_down_length < dot_max:
        buffer.append(DOT)
    elif key_down_length > 2.2*dot_max:
        buffer.append(DASH)
    else:
        buffer.append(UNKNOWN)
        bit_string = "".join(buffer)
        print("\n" + bit_string )
        del buffer[:]
