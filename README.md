# Silentvoice

Silentvoice is a blink-based Morse code communicator and smart room control system. It uses computer vision and machine learning to detect blinks from a webcam, translates them into Morse code, and allows users to send messages or control devices. The system also integrates with ESP32 hardware for home automation.

## Features

- Blink detection using webcam (MediaPipe and dlib)
- Morse code decoding from blinks
- Web interface for messaging and device control
- ESP32 integration for controlling lights, fan, and AC
- User management and message history

## Requirements

- Python 3.12+
- Windows 10/11 (recommended)
- Webcam
- (Optional) ESP32 development board and relay module for room control
- See `requirements.txt` for all Python dependencies

## Installation

1. Clone the repository:
   ```
   git clone <your-repo-url>
   ```
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   pip install dlib-19.24.99-cp312-cp312-win_amd64.whl  # Use provided wheel for dlib
   ```
3. Connect your webcam.
4. (Optional) Set up ESP32 hardware as described in `ESP32_SETUP_README.md`.

## Usage

1. Start the server:
   ```
   python app.py
   ```
2. Open your browser and go to `http://localhost:5000`.
3. Use the web interface to send messages or control devices using blinks.

## Project Structure

- `app.py` - Main application file
- `backend_modules/` - Backend logic (blink detection, communication, etc.)
- `static/` - Frontend assets (CSS, JS)
- `users/` - User data
- `requirements.txt` - Python dependencies
- HTML files - Web interface pages
- `ESP32_SETUP_README.md` - ESP32 hardware setup instructions

## Notes

- For best performance, use a computer with at least 8 GB RAM and a modern CPU. A dedicated GPU is recommended for TensorFlow acceleration but not required.
- Most features work without ESP32 hardware, but room control requires it.
- For mobile/tablet use, consider redeveloping the frontend as a native app (Flutter/React Native) and connect to the backend via API.

## License

MIT License
