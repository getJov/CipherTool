function setupPasswordToggle(inputId, toggleId) {
    const input = document.getElementById(inputId);
    const toggle = document.getElementById(toggleId);

    if (!input || !toggle) {
        return;
    }

    const icon = toggle.querySelector ? toggle.querySelector('i') || toggle : toggle;
    toggle.addEventListener('click', () => {
        const shouldShow = input.type === 'password';
        input.type = shouldShow ? 'text' : 'password';

        icon.classList.toggle('fa-eye', !shouldShow);
        icon.classList.toggle('fa-eye-slash', shouldShow);

        toggle.setAttribute('aria-label', shouldShow ? `Hide ${inputId.replace('-', ' ')}` : `Show ${inputId.replace('-', ' ')}`);
    });
}

function getPasswordFeedback(value) {
    const checks = [
        { met: value.length >= 8, message: '8+ characters' },
        { met: /[A-Za-z]/.test(value), message: 'a letter' },
        { met: /\d/.test(value), message: 'a number' },
        { met: /[@$!%*#?&]/.test(value), message: 'a symbol' },
    ];
    const score = checks.filter((check) => check.met).length;
    const missing = checks.filter((check) => !check.met).map((check) => check.message);

    if (!value) {
        return {
            score: 0,
            text: 'Use 8+ characters with a letter, number, and symbol.',
        };
    }

    if (missing.length === 0) {
        return {
            score,
            text: 'Strong password. It matches the required pattern.',
        };
    }

    return {
        score,
        text: `Add ${missing.join(', ')}.`,
    };
}

function setupPasswordMeter() {
    const passwordInput = document.getElementById('password');
    const meter = document.getElementById('password-meter');
    const meterText = document.getElementById('password-meter-text');

    if (!passwordInput || !meter || !meterText) {
        return;
    }

    function updateMeter() {
        const feedback = getPasswordFeedback(passwordInput.value);
        meter.dataset.strength = String(feedback.score);
        meterText.innerHTML = feedback.text;
    }

    passwordInput.addEventListener('input', updateMeter);
    updateMeter();
}

function setupPasswordMatchIndicator() {
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const matchText = document.getElementById('password-match');

    if (!passwordInput || !confirmPasswordInput || !matchText) {
        return;
    }

    function updateMatchState() {
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        matchText.classList.remove('is-match', 'is-mismatch');

        if (!confirmPassword) {
            matchText.innerHTML = 'Re-enter your password to confirm it matches.';
            return;
        }

        if (password && password === confirmPassword) {
            matchText.classList.add('is-match');
            matchText.innerHTML = 'Passwords match.';
            return;
        }

        matchText.classList.add('is-mismatch');
        matchText.innerHTML = 'Passwords do not match yet.';
    }

    passwordInput.addEventListener('input', updateMatchState);
    confirmPasswordInput.addEventListener('input', updateMatchState);
    updateMatchState();
}

setupPasswordToggle('password', 'password-toggle');
setupPasswordToggle('confirm-password', 'confirm-password-toggle');
setupPasswordMeter();
setupPasswordMatchIndicator();
