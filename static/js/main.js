import { state, elements } from './config.js';
import { setupSocketEvents } from './socketClient.js';
import { initWebcam, stopWebcam } from './webcam.js';
import { initializeNavigation } from './navigation.js';
import { populateUserDropdown, setupUserListeners, updateTimerDisplay, updateStatus } from './ui.js';
import { initGame } from './game.js';

// --- Global Controls ---
export function startCommunication() {
    if (!state.currentSelectedUser) {
        updateStatus("Select a user first.");
        return;
    }

    // Prevent multiple start calls
    if (state.isStreaming) return;

    // 1. Tell backend to load user
    state.socket.emit('select_user', { username: state.currentSelectedUser }, (response) => {
        if (response.status === 'success') {
            // 2. Start Webcam
            initWebcam();
            // 3. Start Backend Stream
            state.currentMode = 'navigation';
            state.socket.emit('start_stream');
            state.socket.emit('set_mode', { mode: 'navigation' });
            
            state.communicationStartTime = Date.now();
            state.timerInterval = setInterval(updateTimerDisplay, 1000);
            
            // Set streaming flag for persistence
            state.isStreaming = true;
            sessionStorage.setItem('isStreaming', 'true');
            
            initializeNavigation();
            
            // Update buttons state if they exist
            const startBtn = document.getElementById('startButton');
            const stopBtn = document.getElementById('stopButton');
            const clearBtn = document.getElementById('clearButton');
            if (startBtn) startBtn.disabled = true;
            if (stopBtn) stopBtn.disabled = false;
            if (clearBtn) clearBtn.disabled = false;

        } else {
            updateStatus(response.message);
        }
    });
}

export function stopCommunication() {
    stopWebcam();
    clearInterval(state.timerInterval);
    state.currentMode = 'idle';
    state.isStreaming = false;
    sessionStorage.setItem('isStreaming', 'false');

    if(state.socket) {
        state.socket.emit('stop_stream');
        state.socket.emit('set_mode', { mode: 'idle' });
    }

    // Update buttons state if they exist
    const startBtn = document.getElementById('startButton');
    const stopBtn = document.getElementById('stopButton');
    const clearBtn = document.getElementById('clearButton');
    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
    if (clearBtn) clearBtn.disabled = true;
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    // Cache common elements
    elements.userSelect = document.getElementById('userSelect');
    elements.statusText = document.getElementById('overallStatusText');

    setupSocketEvents();
    populateUserDropdown();
    setupUserListeners();

    // Page Specific Init
    if (document.body.classList.contains('main-page')) {
        document.getElementById('startButton')?.addEventListener('click', startCommunication);
        document.getElementById('stopButton')?.addEventListener('click', stopCommunication);
        setTimeout(initializeNavigation, 500);
    } 
    else if (document.body.classList.contains('flappy-bird-page')) {
        initGame();
    }
    else {
        // Other pages
        setTimeout(initializeNavigation, 500);
    }

    // Device Control Page: Add ON/OFF button logic
    if (document.body.classList.contains('device-control-page')) {
        // Get device from URL param
        const urlParams = new URLSearchParams(window.location.search);
        const device = urlParams.get('device') || 'light1';
        const onBtn = document.getElementById('onBtn');
        const offBtn = document.getElementById('offBtn');
        if (onBtn) {
            onBtn.addEventListener('click', () => {
                console.log('Sending ON for', device);
                fetch(`/esp32/device/${device}/on`, { method: 'POST' })
                    .then(res => res.json())
                    .then(data => {
                        console.log('ON response:', data);
                        updateStatus(data.message || 'ON command sent');
                    })
                    .catch(err => {
                        console.error('ON request failed', err);
                        updateStatus('Failed to send ON command');
                    });
            });
        }
        if (offBtn) {
            offBtn.addEventListener('click', () => {
                console.log('Sending OFF for', device);
                fetch(`/esp32/device/${device}/off`, { method: 'POST' })
                    .then(res => res.json())
                    .then(data => {
                        console.log('OFF response:', data);
                        updateStatus(data.message || 'OFF command sent');
                    })
                    .catch(err => {
                        console.error('OFF request failed', err);
                        updateStatus('Failed to send OFF command');
                    });
            });
        }
    }

    // --- Auto-Start Camera on Device Control Page ---
    setTimeout(() => {
        if (document.body.classList.contains('device-control-page')) {
            if (!state.currentSelectedUser) {
                updateStatus('No user selected. Please select a user first.');
                window.location.assign('/');
                return;
            }
            // Auto-start the camera and backend stream if not already running
            if (!state.isStreaming || !state.stream || !state.stream.active) {
                state.socket.emit('select_user', { username: state.currentSelectedUser }, (response) => {
                    if (response.status === 'success') {
                        initWebcam((err) => {
                            if (err) {
                                updateStatus('Webcam access failed. Please allow camera access and reload the page.');
                            }
                        });
                        state.currentMode = 'navigation';
                        state.socket.emit('start_stream');
                        state.socket.emit('set_mode', { mode: 'navigation' });
                        state.communicationStartTime = Date.now();
                        state.timerInterval = setInterval(updateTimerDisplay, 1000);
                        state.isStreaming = true;
                        sessionStorage.setItem('isStreaming', 'true');
                    } else {
                        updateStatus('User selection failed. Please try again.');
                        window.location.assign('/');
                    }
                });
            }
        } else if (state.currentSelectedUser) {
            // For other pages, preserve previous logic
            if (!state.isStreaming || !state.stream || !state.stream.active) {
                state.socket.emit('select_user', { username: state.currentSelectedUser }, (response) => {
                    if (response.status === 'success') {
                        initWebcam((err) => {
                            if (err) {
                                updateStatus('Webcam access failed. Please allow camera access and reload the page.');
                            }
                        });
                        state.currentMode = 'navigation';
                        state.socket.emit('start_stream');
                        state.socket.emit('set_mode', { mode: 'navigation' });
                        state.communicationStartTime = Date.now();
                        state.timerInterval = setInterval(updateTimerDisplay, 1000);
                        state.isStreaming = true;
                        sessionStorage.setItem('isStreaming', 'true');
                    } else {
                        updateStatus('User selection failed. Please try again.');
                        window.location.assign('/');
                    }
                });
            }
        }
    }, 500);
});