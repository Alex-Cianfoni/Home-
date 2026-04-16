
import string
import tkinter as tk
from tkinter import messagebox

class Rotor:
    def __init__(self, wiring, turnover):
        self.wiring = wiring
        self.turnover = turnover
        self.position = 0

    def set_position(self, position):
        self.position = position % 26

    def forward(self, char):
        index = (ord(char) - ord('A') + self.position) % 26
        return self.wiring[index]

    def backward(self, char):
        index = (self.wiring.index(char) - self.position + 26) % 26
        return chr(index + ord('A'))

    def rotate(self):
        self.position = (self.position + 1) % 26
        return self.position == ord(self.turnover) - ord('A')

class Reflector:
    def __init__(self, wiring):
        self.wiring = wiring

    def reflect(self, char):
        return self.wiring[ord(char) - ord('A')]

class EnigmaMachine:
    def __init__(self, rotors, reflector):
        self.rotors = rotors
        self.reflector = reflector

    def set_rotors(self, positions):
        for rotor, position in zip(self.rotors, positions):
            rotor.set_position(position)

    def rotate_rotors(self):
        turnover = [rotor.rotate() for rotor in self.rotors]
        return turnover

    def encode_letter(self, letter):
        for i in range(len(self.rotors)-1, -1, -1):
            letter = self.rotors[i].forward(letter)
        letter = self.reflector.reflect(letter)
        for i in range(1, len(self.rotors)):
            letter = self.rotors[i].backward(letter)
        self.rotate_rotors()
        return letter

    def encode_message(self, message):
        message = message.upper()
        encoded_message = []
        for letter in message:
            if letter in string.ascii_uppercase:
                encoded_message.append(self.encode_letter(letter))
            else:
                encoded_message.append(letter)
        return ''.join(encoded_message)

# GUI Implementation
def encode_text():
    message = input_text.get("1.0", tk.END).strip()
    if not message:
        messagebox.showwarning("Input Error", "Please enter a message to encode.")
        return
    encoded_message = enigma.encode_message(message)
    output_text.delete("1.0", tk.END)
    output_text.insert("1.0", encoded_message)

def decode_text():
    message = output_text.get("1.0", tk.END).strip()
    if not message:
        messagebox.showwarning("Input Error", "Please enter a message to decode.")
        return
    decoded_message = enigma.encode_message(message)  # Decoding is just re-encoding
    input_text.delete("1.0", tk.END)
    input_text.insert("1.0", decoded_message)

# Initialize Enigma Machine
rotorI = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", 'Q')
rotorII = Rotor("AJDKSIRUXBLHWTMCQGZNPYFVOE", 'E')
rotorIII = Rotor("BDFHJLCPRTXVZNYEIWGAKMUSQO", 'V')
rotorIV = Rotor("ESOVPZJAYQUIRHXLNFTGKDCMWB", 'J')
reflectorB = Reflector("YRUHQSLDPXNGOKMIEBFZCWVJAT")
enigma = EnigmaMachine([rotorI, rotorII, rotorIII, rotorIV], reflectorB)
enigma.set_rotors([0, 0, 0, 0])

# Create GUI window
root = tk.Tk()
root.title("Enigma Cipher")
root.geometry("400x300")

input_label = tk.Label(root, text="Enter Text:")
input_label.pack()
input_text = tk.Text(root, height=4, width=50)
input_text.pack()

encode_button = tk.Button(root, text="Encode", command=encode_text)
encode_button.pack()

decode_button = tk.Button(root, text="Decode", command=decode_text)
decode_button.pack()

output_label = tk.Label(root, text="Cipher Output:")
output_label.pack()
output_text = tk.Text(root, height=4, width=50)
output_text.pack()

root.mainloop()
