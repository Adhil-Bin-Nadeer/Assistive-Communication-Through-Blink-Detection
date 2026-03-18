class MorseCodeDecoder:
    def __init__(self):
        self.morse_code_dict = {
            '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
            '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
            '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
            '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
            '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
            '--..': 'Z', '.----': '1', '..---': '2', '...--': '3',
            '....-': '4', '.....': '5', '-....': '6', '--...': '7',
            '---..': '8', '----.': '9', '-----': '0', '--..--': ',',
            '.-.-.-': '.', '..--..': '?', '.----.': "'", '-.-.--': '!',
            '-..-.': '/', '-.--.': '(', '-.--.-': ')', '.-...': '&',
            '---...': ':', '-.-.-.': ';', '-...-': '=', '.-.-.': '+',
            '-....-': '-', '..--.-': '_', '.-..-.': '"', '...-..-': '$',
            '.--.-.': '@', '....-...': 'SOS'
        }

    def decode(self, morse_sequence):
        return self.morse_code_dict.get(morse_sequence, '?')

    def get_possible_matches(self, partial_sequence):
        """Returns all morse codes that start with the given partial sequence."""
        matches = {}
        for code, char in self.morse_code_dict.items():
            if code.startswith(partial_sequence):
                matches[code] = char
        return matches