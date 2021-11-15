#!/usr/bin/env python3
"""
Synth

Authors Donald Hau.
requires Python 3.7 or above as dictionaries are ordered

"""

import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
from Adafruit_BBIO.Encoder import RotaryEncoder, eQEP2, eQEP1
import smbus
import time
from dictionaries import seg7_dict, midi_names, midi_freq
import midi

def main():
    play()


class Piano:
    def __init__(self):
        self.lowNote = 36
        self.pos1 = 0
        self.pos2 = 0
        self.current_notes = []
        self.ended = 0
        self.setup()
        

    def setup(self):
        self.pwm_setup()
        self.control_setup()
        self.gpio_setup()
        self.button_setup()
    
    def pwm_setup(self):
        self.pwm_pins = ["P9_22", "P9_14", "P8_19"]
        for pin in self.pwm_pins:
            # print("verified pwm for " + pin)
            PWM.start(pin, 50, 5)
            PWM.stop(pin)
            
    def control_setup(self):
        self.encoder1 = RotaryEncoder(eQEP1)
        self.encoder1.setAbsolute()
        self.encoder1.enable()
        self.encoder1.frequency = 500
        
        self.encoder2 = RotaryEncoder(eQEP2)
        self.encoder2.setAbsolute()
        self.encoder2.enable()
        self.encoder2.frequency = 500
        
    def gpio_setup(self):
        self.buttons = ["P8_14", "P8_15", "P8_16", "P8_17", "P8_18", "P8_26", "P8_27", "P8_28", "P8_29", "P8_30", "P9_23", "P8_32"]

        # Set the GPIO pins:
        for pin in self.buttons:
            GPIO.setup(pin, GPIO.IN)
            # print(GPIO.input(pin))
        
        self.digits = ["P8_34", "P8_36", "P8_37", "P8_38"]
        for pin in self.digits:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1)
            
        self.segments = ["P8_39", "P8_40", "P8_41", "P8_42", "P8_43", "P8_44", "P8_45"]
        for pin in self.segments:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)
    
    def button_setup(self):
        for button in self.buttons:
            # print("added event for "+button)
            GPIO.add_event_detect(button, GPIO.BOTH, callback=self.button_notes)
            
    def write_screen(self, string):
        for j in range(4):
            GPIO.output(self.digits[j], 1)
            for i in range(7):
                GPIO.output(self.segments[i], seg7_dict[string[j]][i])
                #print("digit " + str(j) + " segment " + str(i) + " set to " + str(seg7_dict[string[j]][i]))
            GPIO.output(self.digits[j], 0)
            
    def button_notes(self, button):
        midi_note = self.lowNote + self.buttons.index(button)
        if GPIO.input(button) == True:
            if midi_note not in self.current_notes:
                self.current_notes.append(midi_note)
                
        else: 
            if midi_note in self.current_notes:
                self.current_notes.remove(midi_note)
        self.pwm_update()
    
    def update_notes(self):
        self.current_notes = []
        for button in self.buttons:
            midi_note = self.lowNote + self.buttons.index(button)
            if GPIO.input(button) == True:
                if midi_note not in self.current_notes:
                    self.current_notes.append(midi_note)
            else:
                if midi_note in self.current_notes:
                    self.current_notes.remove(midi_note)
        self.pwm_update()
    
    def pwm_update(self):
        #print(self.current_notes)
        for i in range(3):
            #PWM.stop(self.pwm_pins[i])
            if i < len(self.current_notes):
                PWM.start(self.pwm_pins[i], 50, midi_freq[self.current_notes[i]])
            else:
                PWM.stop(self.pwm_pins[i])
            
            
    def get_position(self):
        self.pos1 = self.encoder1.position
        self.pos2 = self.encoder2.position
    
    def get_input(self):
        if self.encoder1.position > self.pos1:
            if self.lowNote >=12:
                self.lowNote -= 12
        elif self.encoder2.position > self.pos2:
            if self.lowNote > 0:
                self.lowNote -= 1
        elif self.encoder1.position < self.pos1:
            if self.lowNote <= 103:
                self.lowNote += 12
        elif self.encoder2.position < self.pos2:
            if self.lowNote < 115:
                self.lowNote += 1
        else:
            return
        #print(self.lowNote)
        self.get_position()
        self.update_notes()


    def run(self):
        while self.ended == 0:
            #self.write_screen(midi_names[self.lowNote])
            self.get_input()
            

def play():
    instance = Piano()
    instance.run()

main()