
import string
import random

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

# Example usage:
if __name__ == "__main__":
    # Define rotor wirings and turnover notches
    rotorI = Rotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ", 'Q')
    rotorII = Rotor("AJDKSIRUXBLHWTMCQGZNPYFVOE", 'E')
    rotorIII = Rotor("BDFHJLCPRTXVZNYEIWGAKMUSQO", 'V')

    # Define reflector wiring (UKW-B)
    reflectorB = Reflector("YRUHQSLDPXNGOKMIEBFZCWVJAT")

    # Create an Enigma machine with specified rotors and reflector
    enigma = EnigmaMachine([rotorI, rotorII, rotorIII], reflectorB)

    # Set initial rotor positions (for example: A, A, A)
    enigma.set_rotors([0, 0, 0])

    # Encrypt a message
    plaintext = "HELLO WORLD"
    ciphertext = enigma.encode_message(plaintext)
    print(f"Plaintext:  {plaintext}")
    print(f"Ciphertext: {ciphertext}")

