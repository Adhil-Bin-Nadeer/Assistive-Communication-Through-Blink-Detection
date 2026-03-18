import time
import os
from collections import deque
from .morse_decoder import MorseCodeDecoder
from .blink_detector import BlinkDetector
from .classifier import BlinkClassifier
from .esp32_controller import ESP32Controller

class MorseCodeCommunicator:
    def __init__(self, esp32_ip="192.168.1.100"):
        self.blink_detector = BlinkDetector()
        self.morse_decoder = MorseCodeDecoder()
        self.classifier = BlinkClassifier()
        self.current_user = None
        self.esp32 = ESP32Controller(esp32_ip=esp32_ip)
        
        # State variables
        self.current_morse_sequence = ""
        self.message_accum = ""
        self.last_blink_time = 0
        self.last_letter_time = 0
        self.last_blink_type = None
        self.last_blink_timestamp = 0
        self.post_decode_until = 0
        self.last_decoded_char = None

        # Timing Constants (tuned for paralyzed patients)
        self.LETTER_PAUSE = 3.0
        self.SPACE_PAUSE = 5.0
        self.BLINK_COOLDOWN = 0.8
        self.POST_DECODE_PAUSE = 1.5

    def load_user_profile(self, user_info):
        """Loads the classifier for the selected user."""
        if user_info and user_info.get('trained'):
            # Normalize path for cross-platform compatibility
            model_path = os.path.normpath(user_info['model_path'])
            success = self.classifier.load_model(model_path)
            if success:
                print(f"User profile loaded from: {model_path}")
            return success
        return False

    def reset_state(self):
        self.current_morse_sequence = ""
        self.message_accum = ""
        self.last_blink_time = 0
        self.last_letter_time = 0
        self.last_blink_type = None
        self.last_blink_timestamp = 0
        self.post_decode_until = 0
        self.last_decoded_char = None

    def process_blink(self, blink_data, blink_type=None):
        """
        Processes a detected blink with cooldown and post-decode pause enforcement.

        Args:
            blink_data (dict): Contains 'duration', 'timestamp', 'type', etc.
            blink_type (str, optional): 'dot' or 'dash'. If None, will use the type from blink_data.
        """
        current_time = time.time()

        # Enforce blink cooldown - reject blinks too close together
        if (current_time - self.last_blink_timestamp) < self.BLINK_COOLDOWN:
            return "cooldown_rejected", self.current_morse_sequence

        # Enforce post-decode pause - reject blinks during reading period
        if current_time < self.post_decode_until:
            return "post_decode_rejected", self.current_morse_sequence

        self.last_blink_time = current_time
        self.last_blink_timestamp = current_time

        # Get type from blink_data if not explicitly provided
        if blink_type is None:
            blink_type = blink_data.get('type', 'dot')

        self.last_blink_type = blink_type

        if blink_type == 'dot':
            self.current_morse_sequence += "."
        elif blink_type == 'dash':
            self.current_morse_sequence += "-"

        return "blink_added", self.current_morse_sequence

    def handle_time_based_decoding(self):
        """Checks if enough time has passed to decode a letter or add a space."""
        current_time = time.time()
        time_since_blink = current_time - self.last_blink_time

        # Skip all decoding during post-decode reading pause
        if current_time < self.post_decode_until:
            return {
                "status": "post_decode_pause",
                "remaining": self.post_decode_until - current_time
            }

        # 1. Check for Letter Pause (End of sequence -> Decode character)
        if self.current_morse_sequence and time_since_blink > self.LETTER_PAUSE:
            decoded_char = self.morse_decoder.decode(self.current_morse_sequence)
            self.message_accum += decoded_char
            sequence_processed = self.current_morse_sequence
            self.current_morse_sequence = ""
            self.last_letter_time = current_time
            self.last_decoded_char = decoded_char

            # Activate post-decode reading pause
            self.post_decode_until = current_time + self.POST_DECODE_PAUSE

            return {
                "status": "decoded",
                "char": decoded_char,
                "sequence": sequence_processed,
                "message": self.message_accum
            }

        # 2. Check for Space Pause (End of word -> Add space)
        if self.message_accum and not self.message_accum.endswith(' ') and \
           (current_time - self.last_letter_time > self.SPACE_PAUSE) and \
           (self.last_letter_time > 0):
            self.message_accum += " "
            return {"status": "space_added", "message": self.message_accum}

        return {"status": "waiting"}

    def get_predicted_char(self):
        """Returns what the current morse sequence would decode to."""
        if self.current_morse_sequence:
            return self.morse_decoder.decode(self.current_morse_sequence)
        return None

    def clear_message(self):
        """Clear the entire accumulated message."""
        self.message_accum = ""
        self.current_morse_sequence = ""
        self.last_decoded_char = None

    def delete_last_char(self):
        """Delete the last character from the accumulated message."""
        if self.message_accum:
            self.message_accum = self.message_accum[:-1]

    def send_room_control(self, device, action):
        """
        Executes hardware commands via ESP32.
        
        Args:
            device: Device name (e.g., 'light1', 'light2', 'fan', 'ac')
            action: Action to perform ('on', 'off', 'toggle')
            
        Returns:
            Dict with status and message
        """
        result = self.esp32.control_device(device, action)
        return result
    
    def update_esp32_ip(self, new_ip, port=None):
        """Update ESP32 IP address."""
        self.esp32.update_ip(new_ip, port)
        return {"status": "success", "message": f"ESP32 IP updated to {new_ip}"}
    
    def test_esp32_connection(self):
        """Test connection to ESP32."""
        connected, msg = self.esp32.test_connection()
        return {"status": "success" if connected else "error", "message": msg}
    
    def get_device_state(self, device):
        """Get current state of a device."""
        return self.esp32.get_device_state(device)
    
    def get_all_devices(self):
        """Get status of all devices."""
        return self.esp32.get_all_devices()
    
    def turn_all_off(self):
        """Turn off all devices."""
        return self.esp32.turn_all_off()