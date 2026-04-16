import string

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
        # Simple cascade stepping
        rotate_next = self.rotors[-1].rotate()
        for i in range(len(self.rotors)-2, -1, -1):
            if rotate_next:
                rotate_next = self.rotors[i].rotate()
            else:
                break

    def encode_letter(self, letter):
        # Forward through all rotors
        for i in range(len(self.rotors)-1, -1, -1):
            letter = self.rotors[i].forward(letter)
        # Reflect
        letter = self.reflector.reflect(letter)
        # Backward through all rotors
        for i in range(len(self.rotors)):
            letter = self.rotors[i].backward(letter)
        # Rotate rotors after processing
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

# Example usage
if __name__ == "__main__":
    # Define 10 rotor wirings (unique random permutations of A-Z for realism)
    rotor_wirings = [
        "EKMFLGDQVZNTOWYHXUSPAIBRCJ",  # Rotor I
        "AJDKSIRUXBLHWTMCQGZNPYFVOE",  # Rotor II
        "BDFHJLCPRTXVZNYEIWGAKMUSQO",  # Rotor III
        "ESOVPZJAYQUIRHXLNFTGKDCMWB",  # Rotor IV
        "VZBRGITYUPSDNHLXAWMJQOFECK",  # Rotor V
        "JPGVOUMFYQBENHZRDKASXLICTW",  # Rotor VI
        "NZJHGRCXMYSWBOUFAIVLPEKQDT",  # Rotor VII
        "FKQHTLXOCBJSPDZRAMEWNIUYGV",  # Rotor VIII
        "LEYJVCNIXWPBQMDRTAKZGFUHOS",  # Rotor IX
        "FSOKANUERHMBTIYCWLQPZXVGJD",  # Rotor X
    ]

    turnovers = ['Q', 'E', 'V', 'J', 'Z', 'M', 'T', 'R', 'K', 'O']
    rotors = [Rotor(w, t) for w, t in zip(rotor_wirings, turnovers)]

    # Reflector (UKW-B)
    reflectorB = Reflector("YRUHQSLDPXNGOKMIEBFZCWVJAT")

    # Initialize 10-rotor Enigma
    enigma = EnigmaMachine(rotors, reflectorB)

    # Set initial rotor positions (A=0 for all)
    enigma.set_rotors([0]*10)

    # Encrypt a message
    plaintext = "hello this is a test of the new 10 rotor engima amchine that i am making and i want to use it on a xeon phi pcie computer"
    ciphertext = enigma.encode_message(plaintext)
    print(f"Plaintext:  {plaintext}")
    print(f"Ciphertext: {ciphertext}")

    # Prove reversibility: decrypt using same settings
    enigma2 = EnigmaMachine(rotors, reflectorB)
    enigma2.set_rotors([0]*10)
    decoded = enigma2.encode_message(ciphertext)
    print(f"Decoded:    {decoded}")
