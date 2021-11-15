midi = []
notes= []
order= ["C ", "CS", "D ", "DS","E ", "F ", "FS", "G ", "GS", "A ", "AS", "B "]
dictionary = {}
a=440
for x in range(127):
    midi.append(round((a/32)*(2**((x-9)/12)), 2))
    notes.append(order[x%12] + str(int(x/12))+" ")
    dictionary[notes[x]] = midi[x]
print(midi)
print(notes)
print(dictionary)