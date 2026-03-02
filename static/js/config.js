export const state = {
    socket: null,
    stream: null,
    video: null,
    canvas: null,
    ctx: null,
    currentSelectedUser: sessionStorage.getItem('currentSelectedUser') || null,
    currentMode: 'idle', // 'idle', 'navigation', 'morse_input'
    communicationStartTime: null,
    timerInterval: null,
    frameSendingInterval: null,
    isStreaming: sessionStorage.getItem('isStreaming') === 'true'
};

// DOM Elements cache (populated in main.js)
export const elements = {};