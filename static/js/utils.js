/**
 * utils.js
 * General utility functions.
 */

export function speakMessage(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel(); // Stop any current speech
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US';
        window.speechSynthesis.speak(utterance);
    } else {
        console.warn('TTS not supported in this browser.');
    }
}

// --- Tactile Sound Effects (Web Audio API) ---

let _audioCtx = null;

function getAudioContext() {
    if (!_audioCtx) {
        _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    // Resume if suspended (browsers require user gesture to start audio)
    if (_audioCtx.state === 'suspended') {
        _audioCtx.resume();
    }
    return _audioCtx;
}

/**
 * Short, soft tick sound for traversing between options.
 * A brief high-pitched click (1200Hz, 50ms).
 */
export function playTraverseSound() {
    try {
        const ctx = getAudioContext();
        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);

        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(1200, ctx.currentTime);

        gainNode.gain.setValueAtTime(0.15, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.05);

        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.05);
    } catch (e) {
        // Silently ignore audio errors
    }
}

/**
 * Distinct confirmation sound for selecting an option.
 * A two-tone beep (800Hz then 1000Hz, 120ms total) to distinguish from traverse.
 */
export function playSelectSound() {
    try {
        const ctx = getAudioContext();
        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);

        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(800, ctx.currentTime);
        oscillator.frequency.setValueAtTime(1000, ctx.currentTime + 0.06);

        gainNode.gain.setValueAtTime(0.2, ctx.currentTime);
        gainNode.gain.setValueAtTime(0.2, ctx.currentTime + 0.1);
        gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.12);

        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.12);
    } catch (e) {
        // Silently ignore audio errors
    }
}