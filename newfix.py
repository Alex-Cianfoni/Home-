import string
import tkinter as tk
from tkinter import messagebox

class Rotor:
    def __init__(self, wiring, turnover):
        self.wiring = wiring  # e.g. "EKMFL..."
        self.turnover = turnover  # e.g. 'Q'
        self.position = 0  # 0..25

    def set_position(self, position):
        self.position = position % 26

    # Forward path through rotor (right->left)
    def forward(self, char, pos_override=None):
        pos = self.position if pos_override is None else pos_override
        # input index shifted by rotor position
        idx = (ord(char) - ord('A') + pos) % 26
        mapped_char = self.wiring[idx]
        # unshift by position to produce letter passed to next stage
        out_index = (ord(mapped_char) - ord('A') - pos) % 26
        return chr(out_index + ord('A'))

    # Backward path through rotor (left->right)
    def backward(self, char, pos_override=None):
        pos = self.position if pos_override is None else pos_override
        # shift input by position
        effective = (ord(char) - ord('A') + pos) % 26
        # find index i such that wiring[i] == chr(effective + 'A')
        target_char = chr(effective + ord('A'))
        i = self.wiring.index(target_char)
        out_index = (i - pos) % 26
        return chr(out_index + ord('A'))

    # rotate the rotor by one step; return True if its notch causes next rotor to step
    def rotate(self):
        self.position = (self.position + 1) % 26
        return self.position == (ord(self.turnover) - ord('A'))

class Reflector:
    def __init__(self, wiring):
        self.wiring = wiring

    def reflect(self, char):
        return self.wiring[ord(char) - ord('A')]

class EnigmaMachine:
    def __init__(self, rotors, reflector):
        self.rotors = rotors  # left..right order
        self.reflector = reflector

    def set_rotors(self, positions):
        for rotor, position in zip(self.rotors, positions):
            rotor.set_position(position)

    # Stepping logic (simplified standard behavior):
    # - Rightmost rotor always steps.
    # - If a rotor is at its turnover position BEFORE stepping, it causes the rotor to its left to step too.
    def rotate_rotors(self):
        n = len(self.rotors)
        will_step = [False] * n
        # rightmost always steps
        will_step[n-1] = True
        # check notches from right to left to propagate stepping
        # if rotor i is currently at its notch, rotor i-1 will step
        for i in range(n-1, 0, -1):
            if self.rotors[i].position == (ord(self.rotors[i].turnover) - ord('A')):
                will_step[i-1] = True
        # apply steps
        for i in range(n):
            if will_step[i]:
                self.rotors[i].rotate()
        return will_step

    # Encode single letter (this mutates rotor positions because Enigma steps on each keypress)
    def encode_letter(self, letter):
        # Step rotors first (historical Enigma steps before encipher)
        self.rotate_rotors()

        # forward through rotors: right -> left
        ch = letter
        for i in range(len(self.rotors)-1, -1, -1):
            ch = self.rotors[i].forward(ch)

        # reflector
        ch = self.reflector.reflect(ch)

        # backward through rotors: left -> right
        for i in range(0, len(self.rotors)):
            ch = self.rotors[i].backward(ch)

        return ch

    # Encode a whole message: preserves initial rotor positions by saving/restoring
    def encode_message(self, message):
        # save positions so encode_message is non-destructive (you can set positions and call encode twice)
        saved_positions = [r.position for r in self.rotors]

        message = message.upper()
        encoded = []
        for ch in message:
            if ch in string.ascii_uppercase:
                encoded.append(self.encode_letter(ch))
            else:
                encoded.append(ch)

        # restore rotor positions
        for r, p in zip(self.rotors, saved_positions):
            r.position = p

        return ''.join(encoded)

# GUI Implementation
def parse_positions(text):
    # Accept "0 0 0 0", or "A B C D" as letters, or "1,2,3,4"
    text = text.strip()
    if not text:
        return None
    parts = text.replace(',', ' ').split()
    positions = []
    for p in parts:
        if p.isalpha() and len(p) == 1:
            positions.append((ord(p.upper()) - ord('A')) % 26)
        else:
            try:
                positions.append(int(p) % 26)
            except:
                return None
    return positions

def encode_text():
    pos = parse_positions(pos_entry.get())
    if pos and len(pos) == len(enigma.rotors):
        enigma.set_rotors(pos)
    elif pos is not None and len(pos) != len(enigma.rotors):
        messagebox.showwarning("Position Error", f"Enter {len(enigma.rotors)} rotor positions (letters or numbers).")
        return

    message = input_text.get("1.0", tk.END).strip()
    if not message:
        messagebox.showwarning("Input Error", "Please enter a message to encode.")
        return
    encoded_message = enigma.encode_message(message)
    output_text.delete("1.0", tk.END)
    output_text.insert("1.0", encoded_message)

def decode_text():
    pos = parse_positions(pos_entry.get())
    if pos and len(pos) == len(enigma.rotors):
        enigma.set_rotors(pos)
    elif pos is not None and len(pos) != len(enigma.rotors):
        messagebox.showwarning("Position Error", f"Enter {len(enigma.rotors)} rotor positions (letters or numbers).")
        return

    message = output_text.get("1.0", tk.END).strip()
    if not message:
        messagebox.showwarning("Input Error", "Please enter a message to decode.")
        return
    # Enigma is symmetric: encoding again with same start positions decodes
    decoded_message = enigma.encode_message(message)
    input_text.delete("1.0", tk.END)
    input_text.insert("1.0", decoded_message)

# Initialize Enigma Machine (left -> right)
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
root.geometry("520x420")

input_label = tk.Label(root, text="Enter Text:")
input_label.pack()
input_text = tk.Text(root, height=6, width=60)
input_text.pack()

pos_label = tk.Label(root, text=f"Rotor start positions (left->right). Use letters or numbers, e.g. 'A A A A' or '0 0 0 0':")
pos_label.pack()
pos_entry = tk.Entry(root, width=30)
pos_entry.insert(0, "A A A A")
pos_entry.pack(pady=(0,10))

encode_button = tk.Button(root, text="Encode", command=encode_text)
encode_button.pack()

decode_button = tk.Button(root, text="Decode", command=decode_text)
decode_button.pack()

output_label = tk.Label(root, text="Cipher Output:")
output_label.pack()
output_text = tk.Text(root, height=6, width=60)
output_text.pack()

root.mainloop()
