import string
import tkinter as tk
from tkinter import ttk, messagebox

# ---------------- Enigma Core ---------------- #

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
        rotate_next = self.rotors[-1].rotate()
        for i in range(len(self.rotors)-2, -1, -1):
            if rotate_next:
                rotate_next = self.rotors[i].rotate()
            else:
                break

    def encode_letter(self, letter):
        if letter not in string.ascii_uppercase:
            return letter
        for i in range(len(self.rotors)-1, -1, -1):
            letter = self.rotors[i].forward(letter)
        letter = self.reflector.reflect(letter)
        for i in range(len(self.rotors)):
            letter = self.rotors[i].backward(letter)
        self.rotate_rotors()
        return letter

    def encode_message(self, message):
        message = message.upper()
        encoded_message = []
        for letter in message:
            encoded_message.append(self.encode_letter(letter))
        return ''.join(encoded_message)

# ---------------- GUI Section ---------------- #

class EnigmaGUI:
    def __init__(self, master):
        self.master = master
        master.title("10-Rotor Enigma Machine 🌀")
        master.geometry("900x600")
        master.config(bg="#1a1a1a")

        # Define rotors and reflector
        rotor_wirings = [
            "EKMFLGDQVZNTOWYHXUSPAIBRCJ",
            "AJDKSIRUXBLHWTMCQGZNPYFVOE",
            "BDFHJLCPRTXVZNYEIWGAKMUSQO",
            "ESOVPZJAYQUIRHXLNFTGKDCMWB",
            "VZBRGITYUPSDNHLXAWMJQOFECK",
            "JPGVOUMFYQBENHZRDKASXLICTW",
            "NZJHGRCXMYSWBOUFAIVLPEKQDT",
            "FKQHTLXOCBJSPDZRAMEWNIUYGV",
            "LEYJVCNIXWPBQMDRTAKZGFUHOS",
            "FSOKANUERHMBTIYCWLQPZXVGJD",
        ]
        turnovers = ['Q', 'E', 'V', 'J', 'Z', 'M', 'T', 'R', 'K', 'O']
        self.rotors = [Rotor(w, t) for w, t in zip(rotor_wirings, turnovers)]
        reflectorB = Reflector("YRUHQSLDPXNGOKMIEBFZCWVJAT")
        self.enigma = EnigmaMachine(self.rotors, reflectorB)

        # --- UI Components --- #

        tk.Label(master, text="10-Rotor Enigma Machine", font=("Arial", 22, "bold"), fg="cyan", bg="#1a1a1a").pack(pady=10)

        # Rotor position inputs
        rotor_frame = tk.Frame(master, bg="#1a1a1a")
        rotor_frame.pack(pady=10)

        self.rotor_entries = []
        for i in range(10):
            lbl = tk.Label(rotor_frame, text=f"R{i+1}", fg="white", bg="#1a1a1a", font=("Arial", 12))
            lbl.grid(row=0, column=i, padx=5)
            entry = ttk.Entry(rotor_frame, width=3, justify="center")
            entry.insert(0, "A")
            entry.grid(row=1, column=i, padx=5)
            self.rotor_entries.append(entry)

        # Input text box
        tk.Label(master, text="Input Message:", fg="white", bg="#1a1a1a", font=("Arial", 14)).pack(pady=(15, 5))
        self.input_text = tk.Text(master, height=6, width=100, wrap="word", font=("Courier", 12))
        self.input_text.pack(pady=5)

        # Buttons
        button_frame = tk.Frame(master, bg="#1a1a1a")
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Encrypt / Decrypt", command=self.encrypt_message).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Clear", command=self.clear_text).grid(row=0, column=1, padx=10)

        # Output box
        tk.Label(master, text="Output Message:", fg="white", bg="#1a1a1a", font=("Arial", 14)).pack(pady=(10, 5))
        self.output_text = tk.Text(master, height=6, width=100, wrap="word", font=("Courier", 12), fg="black")
        self.output_text.pack(pady=5)
        
    def get_positions(self):
        positions = []
        for e in self.rotor_entries:
            val = e.get().upper()
            if len(val) != 1 or val not in string.ascii_uppercase:
                messagebox.showerror("Invalid Input", "Rotor positions must be single letters A-Z.")
                return None
            positions.append(ord(val) - ord('A'))
        return positions

    def encrypt_message(self):
        positions = self.get_positions()
        if positions is None:
            return
        self.enigma.set_rotors(positions)
        message = self.input_text.get("1.0", tk.END).strip()
        if not message:
            messagebox.showwarning("No Input", "Please enter a message to encode.")
            return
        result = self.enigma.encode_message(message)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, result)

    def clear_text(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)

# ---------------- Run App ---------------- #

if __name__ == "__main__":
    root = tk.Tk()
    app = EnigmaGUI(root)
    root.mainloop()
