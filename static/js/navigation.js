import { state } from './config.js';
import { stopCommunication, startCommunication } from './main.js';
import { speakMessage, playTraverseSound, playSelectSound } from './utils.js';

let navigableElements = [];
let currentNavIndex = -1;

function getElementLabel(el) {
    return el.dataset.tts
        || el.dataset.text
        || el.querySelector('.yesno-text, .text')?.innerText?.trim()
        || el.innerText?.trim()
        || 'item';
}

function updateYesNoPrompt(el) {
    // No message display on yes/no page - user relies on visual highlight only
}

export function initializeNavigation() {
    navigableElements = [];
    currentNavIndex = -1;

    // Selectors based on page
    if (document.body.classList.contains('main-page')) {
        navigableElements = Array.from(document.querySelectorAll('.nav-button, .control-button'));
    } else if (document.body.classList.contains('room-control-page')) {
        navigableElements = Array.from(document.querySelectorAll('.device-button'));
    } else if (document.body.classList.contains('quick-messages-page')) {
        // Includes quick message buttons AND the back/start buttons
        navigableElements = Array.from(document.querySelectorAll('.quick-message-button, #backButton, #startQuickMsgButton'));
    } else if (document.body.classList.contains('device-control-page')) {
        navigableElements = Array.from(document.querySelectorAll('.device-button'));
    } else if (document.body.classList.contains('yesno-page')) {
        navigableElements = Array.from(document.querySelectorAll('.yesno-button'));
    }

    if (navigableElements.length > 0) setHighlight(0);
}

export function setHighlight(index) {
    navigableElements.forEach(el => el.classList.remove('highlighted'));
    currentNavIndex = index;
    if (navigableElements[currentNavIndex]) {
        const activeElement = navigableElements[currentNavIndex];
        activeElement.classList.add('highlighted');
        activeElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        updateYesNoPrompt(activeElement);
    }
}

export function moveHighlight(direction) {
    if (navigableElements.length === 0) return;
    let newIndex = (currentNavIndex + direction + navigableElements.length) % navigableElements.length;
    setHighlight(newIndex);
    playTraverseSound();
}

export function selectHighlightedElement() {
    if (currentNavIndex < 0 || !navigableElements[currentNavIndex]) return;
    const el = navigableElements[currentNavIndex];
    const isYesNoPage = document.body.classList.contains('yesno-page');

    if (!isYesNoPage) {
        el.classList.remove('highlighted');
    }

    console.log(`Selected: ${el.id || el.innerText}`);

    // Handle generic links (<a> tags)
    if (el.tagName === 'A') {
        playSelectSound();
        window.location.assign(el.href);
        return;
    }

    // --- Specific Logic ---

    // 1. Check for Back Button FIRST to ensure navigation happens
    if (el.id === 'backBtn' || el.id === 'backButton') {
        playSelectSound();
        window.location.assign('/');
        return;
    }

    // 2. Yes/No page buttons (TTS for Yes/No)
    else if (el.classList.contains('yesno-button')) {
        const ttsText = el.dataset.tts;

        if (ttsText) {
            // Yes or No - speak via TTS (no select sound since TTS provides audio feedback)
            speakMessage(ttsText);
        }
        // Back button on yesno page is handled by the backBtn check above
    }

    // 3. Main Page Start/Stop
    else if (el.id === 'startButton') {
        playSelectSound();
        startCommunication();
    }
    else if (el.id === 'stopButton') {
        playSelectSound();
        stopCommunication();
    }
    else if (el.id === 'navMessageBtn' && document.body.classList.contains('main-page')) {
        playSelectSound();
        state.currentMode = 'morse_input';
        state.socket.emit('set_mode', { mode: 'morse_input' });
    }

    // 4. Quick Messages (Text to Speech - no select sound needed)
    else if (el.classList.contains('quick-message-button')) {
        const textElement = el.querySelector('.text');
        if (textElement) {
            const text = textElement.innerText;
            speakMessage(text);
            if (document.getElementById('messageDisplay')) {
                 document.getElementById('messageDisplay').innerText = `Selected: ${text}`;
            }
        }
    }

    // 5. Device Control
    else if (el.dataset.device) {
        playSelectSound();
        window.location.assign(`/devicecontrol.html?device=${el.dataset.device}`);
    }

    // 6. Device control page ON/OFF buttons
    else if (document.body.classList.contains('device-control-page') && el.dataset.action) {
        playSelectSound();
        el.click();
        return;
    }

    else {
        playSelectSound();
    }

    // Auto-advance highlight after selection (unless we just navigated away)
    if (
        state.currentMode !== 'morse_input'
        && el.tagName !== 'A'
        && el.id !== 'backButton'
        && el.id !== 'backBtn'
        && !isYesNoPage
    ) {
        moveHighlight(1);
    }
}
