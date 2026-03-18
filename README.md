# SilentVoice

A blink-based communication system designed for paralyzed patients. SilentVoice uses computer vision and machine learning to detect eye blinks from a webcam, translates them into Morse code, and enables users to compose messages or control room devices — all without any physical movement.

## Features

- **Blink-to-Morse Communication** — Short blinks produce dots (.), long blinks produce dashes (-). The system auto-decodes Morse sequences into letters after a configurable pause.
- **Real-time Morse Reference** — On-screen chart with all 26 letters and 10 numbers. Matching codes highlight as the user blinks.
- **Text-to-Speech** — Composed messages can be spoken aloud via the browser.
- **Quick Messages** — Pre-set common phrases for fast communication.
- **Yes/No Mode** — Simple binary selection via blinks.
- **Room Control** — Control lights, fan, and AC via ESP32 integration.
- **Flappy Bird Game** — Blink-controlled game for entertainment and practice.
- **User Profiles** — Per-user trained blink classifiers for accuracy.

## Requirements

- Python 3.11 or 3.12
- Webcam
- Windows 10/11 (tested)
- (Optional) ESP32 board with relay module for room control

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/SilentVoice.git
   cd SilentVoice
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # Linux/Mac
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install dlib**
   ```bash
   # Use the included pre-built wheel (Python 3.12, Windows x64):
   pip install dlib-19.24.99-cp312-cp312-win_amd64.whl

   # Or install from PyPI (requires CMake and C++ compiler):
   # pip install dlib
   ```

5. **Verify the face landmark model exists**

   The file `shape_predictor_68_face_landmarks.dat` should be in the project root. It is included in the repository.

## Contribution Workflow

To keep the `main` branch stable, every contributor should create a personal working branch from the latest `main` branch and do all development there. Do not make changes directly in `main`.

1. **Update your local `main` branch before starting**
   ```bash
   git switch main
   git pull origin main
   ```
   This makes sure your work starts from the latest approved code in the repository.

2. **Create your own branch from `main` and switch to it**
   ```bash
   git switch -c your-name/short-description
   ```
   Example branch names: `adhil/blink-ui-update`, `john/morse-decoder-fix`

3. **If your branch already exists, switch to your branch in the terminal**
   ```bash
   git switch your-name/short-description
   git pull origin your-name/short-description
   ```
   Do all your changes only in your own branch.

4. **Do your work in your branch**
   Make the required changes in your branch and keep the existing functionality working correctly.

5. **Check your changes and commit them**
   ```bash
   git status
   git add .
   git commit -m "Describe your change clearly"
   ```

6. **Push your branch to GitHub**
   ```bash
   git push -u origin your-name/short-description
   ```
   After the first push, future updates can be pushed with:
   ```bash
   git push
   ```

7. **Pull the latest `main` branch changes into your branch before review**
   ```bash
   git switch main
   git pull origin main
   git switch your-name/short-description
   git merge main
   ```
   If the merge is successful, push the updated branch:
   ```bash
   git push
   ```

8. **If a merge conflict happens, resolve it carefully**
   Git will mark the conflicted files. Open each conflicted file, review both changes carefully, keep the correct code, and remove the conflict markers:
   ```text
   <<<<<<< HEAD
   =======
   >>>>>>> main
   ```
   After resolving the conflict, run:
   ```bash
   git status
   git add <resolved-files>
   git commit -m "Resolve merge conflict"
   git push
   ```
   Always test the project again after resolving conflicts.

9. **Verify your branch before creating a pull request**
   Before requesting a merge to `main`, verify that:
   - The application starts correctly with `python app.py`
   - The app opens successfully at `http://localhost:5000`
   - User creation and blink training still work if your change affects them
   - The feature you changed works as expected
   - Existing pages related to your change still work without errors
   - No important existing functionality is broken by your changes

10. **Open a pull request**
    Push your latest changes and create a pull request from `your-name/short-description` into `main`.
    In the pull request, clearly mention:
    - What you changed
    - Why you changed it
    - What verification you completed
    - Any known limitations or follow-up work

11. **Merge into `main` only after review and verification**
    The branch should be merged into `main` only after the pull request has been reviewed, the changes have been verified, and the work has been confirmed not to break existing functionality.

12. **If your team merges through the terminal, use an approved branch after review**
    Only an authorized maintainer should merge to `main` through the terminal after the pull request is approved.
    ```bash
    git switch main
    git pull origin main
    git merge your-name/short-description
    git push origin main
    ```
    After the merge, pull the latest `main` branch again in any local copies so everyone has the updated code.

## Usage

1. **Start the server**
   ```bash
   python app.py
   ```

2. **Open the app** at [http://localhost:5000](http://localhost:5000)

3. **Create a user** on the dashboard and train the blink classifier by following the on-screen prompts.

4. **Navigate using blinks:**
   - **Short blink (dot)** — Move highlight to next option
   - **Long blink (dash)** — Select highlighted option

5. **Morse code input** — On the message page, blink to input dots and dashes. The system auto-decodes each letter after a 3-second pause and adds a space after a 5-second pause.

## ESP32 Room Control (Optional)

1. Flash your ESP32 with firmware that exposes HTTP endpoints for device control.
2. Update the ESP32 IP address in `backend_modules/config.py`:
   ```python
   ESP32_CONFIG = {
       "ip": "YOUR_ESP32_IP",
       "port": 80,
       ...
   }
   ```
3. The room control page will let you toggle lights, fan, and AC via blinks.

## Project Structure

```
SilentVoice/
├── app.py                       # Flask + SocketIO server
├── Train.py                     # CLI script to train blink classifier
├── requirements.txt             # Python dependencies
├── shape_predictor_68_face_landmarks.dat  # dlib face landmark model
│
├── backend_modules/
│   ├── blink_detector.py        # Eye blink detection (MediaPipe + dlib)
│   ├── classifier.py            # TensorFlow blink classifier (dot vs dash)
│   ├── communicator.py          # Blink → Morse → Message pipeline
│   ├── morse_decoder.py         # Morse code dictionary and decoder
│   ├── esp32_controller.py      # HTTP client for ESP32 device control
│   ├── user_manager.py          # User profile management (JSON)
│   └── config.py                # ESP32 configuration
│
├── static/
│   ├── style.css                # Stylesheet
│   └── js/
│       ├── main.js              # App entry point and page init
│       ├── config.js            # Shared state
│       ├── socketClient.js      # Socket.IO event handling
│       ├── ui.js                # DOM updates and morse display
│       ├── navigation.js        # Blink-based UI navigation
│       ├── webcam.js            # Webcam capture and frame streaming
│       ├── utils.js             # Text-to-speech utilities
│       └── game.js              # Flappy Bird game logic
│
├── index.html                   # Dashboard
├── message.html                 # Morse code input page
├── quick_messages.html          # Pre-set quick messages
├── roomcontrol.html             # Room control (device list)
├── devicecontrol.html           # Individual device ON/OFF
├── yesno.html                   # Yes/No selection
├── flappy_bird.html             # Flappy Bird game
│
└── users/
    └── users.json               # User registry and profiles
```

## How It Works

1. **Webcam frames** are captured in the browser and sent to the Flask server via Socket.IO.
2. **Blink detection** uses MediaPipe Face Mesh and dlib's 68-point face landmarks to compute the Eye Aspect Ratio (EAR).
3. When a blink is detected, its **duration** determines whether it is a dot (short) or dash (long), using a TensorFlow-trained classifier.
4. The **Morse decoder** accumulates dots and dashes, then auto-decodes after a letter pause (3s) or inserts a space after a word pause (5s).
5. The decoded message is displayed in real-time on the frontend and can be spoken aloud via the browser's Speech Synthesis API.

## License

MIT License
