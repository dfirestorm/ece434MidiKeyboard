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
from dictionaries import midi_names, midi_freq
from midi import MidiConnector, NoteOn, NoteOff, Message

def main():
    play()


class Piano:
    def __init__(self):
        self.lowNote = 36
        self.pos1 = 0
        self.pos2 = 0
        self.current_notes = []
        self.active_notes = 0
        self.ended = 0
        self.setup()
        

    def setup(self):
        self.pwm_setup()
        self.control_setup()
        self.gpio_setup()
        self.button_setup()
        self.midi_setup()
    
    def pwm_setup(self):
        self.pwm_pins = ["P9_22", "P9_14", "P8_19"]
        for pin in self.pwm_pins:
            # print("verified pwm for " + pin)
            PWM.stop(pin)
            PWM.start(pin, 50, 5)
            PWM.set_frequency(pin, 1)
            PWM.set_duty_cycle(pin, 0)
            
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

    
    def button_setup(self):
        for button in self.buttons:
            # print("added event for "+button)
            GPIO.add_event_detect(button, GPIO.BOTH, callback=self.button_press)
    
    def midi_setup(self):
        self.conn=MidiConnector('/dev/ttyO0')
    
    #def write_screen(self, string):
        
            
    def button_press(self, button):
        midi_note = self.lowNote + self.buttons.index(button)
        if GPIO.input(button) and midi_note not in self.current_notes:
            self.current_notes.append(midi_note)
            self.conn.write(Message(NoteOn(midi_note, 1), channel=1))
        elif midi_note in self.current_notes:
            self.current_notes.remove(midi_note)
            self.conn.write(Message(NoteOff(midi_note, 1), channel=1))
        self.pwm_update()
    
    def update_notes(self):
        self.current_notes = []
        for button in self.buttons:
            midi_note = self.lowNote + self.buttons.index(button)
            if GPIO.input(button) and midi_note not in self.current_notes:
                self.current_notes.append(midi_note)
                self.conn.write(Message(NoteOn(midi_note, 1), channel=1))
            elif midi_note in self.current_notes:
                self.current_notes.remove(midi_note)
                self.conn.write(Message(NoteOff(midi_note, 1), channel=1))
        self.pwm_update()
    
    def pwm_update(self):
        #print(self.current_notes)
        for i in range(3):
            #PWM.stop(self.pwm_pins[i])
            if i < len(self.current_notes):
                PWM.set_frequency(self.pwm_pins[i], midi_freq[self.current_notes[i]])
                PWM.set_duty_cycle(self.pwm_pins[i], 50)
            else:
                PWM.set_frequency(self.pwm_pins[i], 1)
                PWM.set_duty_cycle(self.pwm_pins[i], 0)
                #PWM.stop(self.pwm_pins[i])
            
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
        while True:
            #self.write_screen(midi_names[self.lowNote])
            self.get_input()
            time.sleep(0.05)
            

def play():
    instance = Piano()
    instance.run()
    PWM.cleanup()

main()
