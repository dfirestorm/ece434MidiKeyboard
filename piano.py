#!/usr/bin/env python3
"""
Synth

Authors Donald Hau.
requires Python 3.7 or above as dictionaries are ordered

"""

import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
from Adafruit_BBIO.Encoder import RotaryEncoder, eQEP2, eQEP1
# import smbus 
import time
from midi import MidiConnector, NoteOn, NoteOff, Message
from dictionaries import midi_names, midi_freq # local file


def main():
    instance = Piano()
    instance.run() #this will run forever until it gets killed
    PWM.cleanup() # stops all PWM 
    

class Piano:
    def __init__(self):
        self.lowNote = 36 # starting leftmost note on the buttons, corresponds to C4
        self.pos1 = 0 # position of encoder 1 - modulates octaves
        self.pos2 = 0 # position of encoder 2 - modulates notes
        self.current_notes = [] # array used to keep track of the notes currently being played
        self.ended = 0 # for adding an exit routine if desired
        self.setup() # sets up all pins and functions
        

    def setup(self):
        # all of these do what they say on the tin
        self.pwm_setup()
        self.encoder_setup()
        self.button_setup()
        self.midi_setup()
        # self.display_setup() # not implemented yet
    
    def pwm_setup(self):
        self.num_buzzers = 3
        self.pwm_pins = ["P9_22", "P9_14", "P8_19"]
        for pin in self.pwm_pins:
            # print("verified pwm for " + pin) # for debug
            PWM.stop(pin) # stop any current PWMs running
            PWM.start(pin, 50, 5) # start PWM
            PWM.set_frequency(pin, 1) #set freq to minimum
            PWM.set_duty_cycle(pin, 0) # turn off without a PWM.start since it's slow
            
    def encoder_setup(self):
        self.encoder1 = RotaryEncoder(eQEP1)
        self.encoder1.setAbsolute()
        self.encoder1.enable()
        self.encoder1.frequency = 500
        
        self.encoder2 = RotaryEncoder(eQEP2)
        self.encoder2.setAbsolute()
        self.encoder2.enable()
        self.encoder2.frequency = 500
        
    def button_setup(self):
        self.buttons = ["P8_14", "P8_15", "P8_16", "P8_17", "P8_18", "P8_26", "P8_27", "P8_28", "P8_29", "P8_30", "P8_32", "P8_34"] 
        # these pins conflict with HDMI

        # Set the GPIO pins:
        for pin in self.buttons:
            GPIO.setup(pin, GPIO.IN)
            # print(GPIO.input(pin)) # for debug if a note is playing without pressing the button
        
        # button inputs are callback based and so interrupt other things
        for button in self.buttons:
            # print("added event for "+button) # for debug if an error for 17: file exists is thrown
            GPIO.add_event_detect(button, GPIO.BOTH, callback=self.button_press)
        
    def midi_setup(self):
        # simple setup, opens and starts midi on serial port
        self.conn=MidiConnector('/dev/ttyO0')
    
    # def display_setup(self):
        # for startup of display
        # not implemented yet
    
    # def write_screen(self, string):
        # for if you'd like to display the note currently at the bottom of the keys
        # not implemented yet
        
            
    def button_press(self, button):
        # on button press or release, calculate the midi note it corresponds to
        midi_note = self.lowNote + self.buttons.index(button)
        # if button was pressed and wasn't a false firing
        if GPIO.input(button) and midi_note not in self.current_notes:
            # start playing note and tell midi that note has been pressed
            self.current_notes.append(midi_note)
            self.conn.write(Message(NoteOn(midi_note, 1), channel=1))
        # if button released and is currently playing
        elif midi_note in self.current_notes:
            # stop playing note and tell midi that note has been released
            self.current_notes.remove(midi_note)
            self.conn.write(Message(NoteOff(midi_note, 1), channel=1))
            
        #this function updates the buzzers to the notes that should be playing
        self.pwm_update()
    
    def update_notes(self):
        # if shift key via encoder, buttons no longer correspond so clear current notes
        self.current_notes = []
        #check all buttons for press
        # literally a copy of button_press, but without the pwm_update every time
        for button in self.buttons:
            midi_note = self.lowNote + self.buttons.index(button)
            if GPIO.input(button) and midi_note not in self.current_notes:
                self.current_notes.append(midi_note)
                self.conn.write(Message(NoteOn(midi_note, 1), channel=1))
            elif midi_note in self.current_notes:
                self.current_notes.remove(midi_note)
                self.conn.write(Message(NoteOff(midi_note, 1), channel=1))
        #pwm_update after all notes are updated
        self.pwm_update()
        # self.write_screen(midi_names[self.lowNote]) # update screen
    
    def pwm_update(self):
        #this function updates the buzzers to the notes that should be playing
        #print(self.current_notes) # for debug
        for i in range(self.num_buzzers):
            #check if a note should be playing on that buzzer
            if i < len(self.current_notes):
                # start playing note
                # don't use PWM.start, it adds noticeable delay
                # get frequency from list 
                PWM.set_frequency(self.pwm_pins[i], midi_freq[self.current_notes[i]])
                # 50% duty cycle for piezoelectric buzzers
                PWM.set_duty_cycle(self.pwm_pins[i], 50)
            else:
                 # set freq to 1 since it can't be 0
                 # not strictly necessary due to duty cycle
                PWM.set_frequency(self.pwm_pins[i], 1)
                # turn off PWM via duty cycle without needing a PWM.start later
                PWM.set_duty_cycle(self.pwm_pins[i], 0)
                #PWM.stop(self.pwm_pins[i])
            
    def get_position(self):
        #simple updating of encoders stored positions
        self.pos1 = self.encoder1.position
        self.pos2 = self.encoder2.position
    
    def get_input(self):
        #check encoder positions vs stored positions
        if self.encoder1.position == self.pos1 and self.encoder2.position == self.pos2:
            return # do nothing if positions haven't changed
        # encoder 1 modulates octaves
        if self.encoder1.position > self.pos1 and self.lowNote >=12:
                self.lowNote -= 12
        elif self.encoder1.position < self.pos1 and self.lowNote <= (127-24):
                self.lowNote += 12
        # encoder 2 modulates individual half steps
        if self.encoder2.position > self.pos2 and self.lowNote > 0:
                self.lowNote -= 1
        elif self.encoder2.position < self.pos2 and self.lowNote < (127-12):
                self.lowNote += 1
        # due to return above, only activates if an encoder moved
        #print(self.lowNote)
        self.get_position() # update encoder stored positions
        self.update_notes() # update notes being played


    def run(self):
        while self.ended == 0:
            # self.ended not implemented but if you wanted an off button you could add it here
            self.get_input() # check encoders for changes
            # helpful if you get double inputs on encoders, adjust as necessary
            time.sleep(0.05)
            

main()
