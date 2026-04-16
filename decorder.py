ciphertext = "QVVQF GROU UQ N KQWF XI YQJ ZNA 10 QFXNV CXLJQM RPTLPFM EWWY G QH XPVDRB FIY M BVVY LQ KGG CF CB M DDPO YFM NEHI WMYJGFSD"

# re-create the same 10 rotors, reflector, and positions as before
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
    "FSOKANUERHMBTIYCWLQPZXVGJD"
]
turnovers = ['Q','E','V','J','Z','M','T','R','K','O']
rotors = [Rotor(w, t) for w, t in zip(rotor_wirings, turnovers)]
reflectorB = Reflector("YRUHQSLDPXNGOKMIEBFZCWVJAT")

enigma = EnigmaMachine(rotors, reflectorB)
enigma.set_rotors([0]*10)   # <-- must match your original starting positions

decoded = enigma.encode_message(ciphertext)
print("Decoded message:", decoded)