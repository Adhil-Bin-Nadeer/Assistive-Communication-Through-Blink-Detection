import os
import sys
import threading
import time

from flask import Flask, send_from_directory, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import numpy as np
import base64
import cv2

# Import modular backend components
from backend_modules.user_manager import UserManager
from backend_modules.communicator import MorseCodeCommunicator
from backend_modules.config import ESP32_CONFIG

# --- Configuration ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(ROOT_DIR, 'frontend', 'dist')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_change_in_production'

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    max_http_buffer_size=10 * 1024 * 1024
)

# Global Instances
user_manager = UserManager()
communicator = MorseCodeCommunicator(esp32_ip=ESP32_CONFIG.get('ip', '192.168.1.100'))
communicator.user_manager = user_manager

# Global processing state
processing_thread = None
thread_lock = threading.Lock()
processing_active = False
current_frame = None

# ---------------------------------------------------------------------------
# User API
# ---------------------------------------------------------------------------

@app.route('/users')
def list_users_api():
    users = user_manager.list_users()
    user_data = {}
    for u in users:
        info = user_manager.get_user(u)
        user_data[u] = {'trained': info.get('trained', False) if info else False}
    return jsonify(user_data)


@app.route('/create_user/<username>')
def create_user_api(username):
    if user_manager.add_user(username):
        return jsonify({"status": "success", "message": f"User '{username}' created."})
    return jsonify({"status": "error", "message": "User exists."}), 409


# ---------------------------------------------------------------------------
# ESP32 Control API
# ---------------------------------------------------------------------------

@app.route('/esp32/test')
def test_esp32():
    result = communicator.test_esp32_connection()
    return jsonify(result)


@app.route('/esp32/config', methods=['GET'])
def get_esp32_config():
    return jsonify({
        "ip": ESP32_CONFIG.get('ip'),
        "port": ESP32_CONFIG.get('port'),
        "devices": ESP32_CONFIG.get('devices')
    })


@app.route('/esp32/config', methods=['POST'])
def update_esp32_config():
    data = request.json
    new_ip = data.get('ip')
    new_port = data.get('port')
    if not new_ip:
        return jsonify({"status": "error", "message": "IP address required"}), 400
    result = communicator.update_esp32_ip(new_ip, new_port)
    ESP32_CONFIG['ip'] = new_ip
    if new_port:
        ESP32_CONFIG['port'] = new_port
    return jsonify(result)


@app.route('/esp32/devices')
def get_all_devices():
    result = communicator.get_all_devices()
    return jsonify(result)


@app.route('/esp32/device/<device>/<action>', methods=['POST'])
def control_esp32_device(device, action):
    try:
        client = request.remote_addr
        print(f"[DeviceControl] {client}: device={device}, action={action}")
        result = communicator.send_room_control(device, action)
        print(f"[DeviceControl] result: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"[DeviceControl] Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/esp32/device/<device_name>')
def get_device_state(device_name):
    result = communicator.get_device_state(device_name)
    return jsonify(result)


@app.route('/esp32/alloff')
def turn_all_off():
    result = communicator.turn_all_off()
    return jsonify(result)


# ---------------------------------------------------------------------------
# Socket.IO Events
# ---------------------------------------------------------------------------

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')


@socketio.on('disconnect')
def handle_disconnect():
    global processing_active
    print(f'Client disconnected: {request.sid}')
    processing_active = False


@socketio.on('select_user')
def handle_select_user(data):
    username = data.get('username')
    user_info = user_manager.get_user(username)
    if not user_info:
        return {'status': 'error', 'message': 'User not found'}
    communicator.current_user = username
    if communicator.load_user_profile(user_info):
        return {'status': 'success', 'message': f"User {username} loaded"}
    return {'status': 'success', 'message': f"User {username} selected (Not trained)"}


@socketio.on('set_mode')
def set_mode(data):
    mode = data.get('mode')
    print(f"Mode switched to: {mode}")
    if mode == 'idle':
        communicator.reset_state()


@socketio.on('start_stream')
def start_stream():
    global processing_active, processing_thread
    if not processing_active:
        processing_active = True
        processing_thread = socketio.start_background_task(process_frames, request.sid)
        emit('stream_started', {'message': 'Backend processing started'})


@socketio.on('stop_stream')
def stop_stream():
    global processing_active
    processing_active = False
    emit('stream_stopped', {'message': 'Backend processing stopped'})


@socketio.on('send_quick_message')
def handle_quick_message(data):
    msg = data.get('message')
    print(f"Quick Message: {msg}")
    emit('status', {'message': f"Sent: {msg}"})


@socketio.on('room_command')
def handle_room_command(data):
    device = data.get('device')
    action = data.get('action')
    result = communicator.send_room_control(device, action)
    emit('status', {'message': result['message']})


@socketio.on('clear_message')
def handle_clear_message():
    communicator.clear_message()
    _update_ui(request.sid)
    emit('message_cleared', {'status': 'success'})


@socketio.on('delete_last_char')
def handle_delete_last():
    communicator.delete_last_char()
    _update_ui(request.sid)
    emit('char_deleted', {'status': 'success', 'message': communicator.message_accum})


@socketio.on('speak_message')
def handle_speak_message():
    emit('do_speak', {'message': communicator.message_accum})


@socketio.on('frame')
def handle_frame(data):
    global current_frame
    try:
        if 'image' in data:
            img_str = data['image']
            if ',' in img_str:
                img_str = img_str.split(',')[1]
            img_bytes = base64.b64decode(img_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            current_frame = frame
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Background frame processing
# ---------------------------------------------------------------------------

def process_frames(sid):
    global processing_active, current_frame
    print(f"Background processing loop started for SID: {sid}")
    last_ui_update = 0

    while processing_active:
        socketio.sleep(0.02)

        if current_frame is None:
            continue

        frame = current_frame.copy()

        blink_info, current_ear = communicator.blink_detector.detect_blink(frame)

        if blink_info:
            blink_type = blink_info.get('type', 'dot')
            print(f"Detected: {blink_type} ({blink_info['duration']:.2f}s)")
            socketio.emit('blink_detected', {
                'type': blink_type,
                'duration': blink_info['duration']
            }, room=sid)
            status, result = communicator.process_blink(blink_info, blink_type)
            if status == "blink_added":
                _update_ui(sid)

        decode_result = communicator.handle_time_based_decoding()
        if decode_result["status"] in ["decoded", "space_added"]:
            print(f"Decoded: {decode_result.get('char', 'SPACE')}")
            _update_ui(sid)

        # Continuous UI updates for timer animation (every 200ms)
        current_time = time.time()
        if (current_time - last_ui_update) > 0.2:
            if communicator.current_morse_sequence or communicator.last_letter_time > 0:
                _update_ui(sid)
            last_ui_update = current_time


def _update_ui(sid):
    current_time = time.time()
    predicted = communicator.get_predicted_char()
    is_in_post_decode = current_time < communicator.post_decode_until

    socketio.emit('update_ui', {
        'message': communicator.message_accum,
        'morse_sequence': communicator.current_morse_sequence,
        'predicted_char': predicted,
        'last_blink_type': communicator.last_blink_type,
        'last_decoded_char': communicator.last_decoded_char,
        'status': 'Processing',
        'letter_timer': max(0, communicator.LETTER_PAUSE - (current_time - communicator.last_blink_time))
                        if communicator.current_morse_sequence else 0,
        'space_timer': max(0, communicator.SPACE_PAUSE - (current_time - communicator.last_letter_time))
                       if communicator.last_letter_time > 0 else 0,
        'post_decode_remaining': max(0, communicator.post_decode_until - current_time),
        'is_in_post_decode': is_in_post_decode,
        'letter_pause_total': communicator.LETTER_PAUSE,
        'space_pause_total': communicator.SPACE_PAUSE,
    }, room=sid)


# ---------------------------------------------------------------------------
# Serve pages and static files
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return send_file(os.path.join(ROOT_DIR, 'index.html'))


@app.route('/message.html')
def message_page():
    return send_file(os.path.join(ROOT_DIR, 'message.html'))


@app.route('/quick_messages')
def quick_messages():
    return send_file(os.path.join(ROOT_DIR, 'quick_messages.html'))


@app.route('/roomcontrol.html')
def room_control():
    return send_file(os.path.join(ROOT_DIR, 'roomcontrol.html'))


@app.route('/devicecontrol.html')
def device_control():
    return send_file(os.path.join(ROOT_DIR, 'devicecontrol.html'))


@app.route('/yesno')
def yesno():
    return send_file(os.path.join(ROOT_DIR, 'yesno.html'))


@app.route('/flappy_bird')
def flappy_bird():
    return send_file(os.path.join(ROOT_DIR, 'flappy_bird.html'))


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(os.path.join(ROOT_DIR, 'static'), path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("Starting Blink Communicator Server...")
    print(f"Serving pages from: {ROOT_DIR}")
    if '--ssl' in sys.argv:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True,
                     ssl_context=('cert.pem', 'key.pem'))
    else:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
