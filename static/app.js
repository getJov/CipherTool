const cipherSelect = document.getElementById('cipher');
const keyDiv = document.getElementById('key-div');
const keywordDiv = document.getElementById('keyword-div');
const submitButton = document.getElementById('cipher-submit');
const modeRadios = document.querySelectorAll('input[name="encrypt_or_decrypt"]');

function updateCipherFields() {
    if (!cipherSelect || !keyDiv || !keywordDiv) {
        return;
    }

    const selectedCipher = cipherSelect.value;

    keyDiv.style.display = selectedCipher === 'caesar' ? 'grid' : 'none';
    keywordDiv.style.display = selectedCipher === 'vigenere' ? 'grid' : 'none';
}

function updateSubmitText() {
    if (!submitButton) {
        return;
    }

    const selectedMode = document.querySelector('input[name="encrypt_or_decrypt"]:checked');
    submitButton.innerHTML = selectedMode && selectedMode.value === 'd' ? 'Decrypt message' : 'Encrypt message';
}

if (cipherSelect) {
    cipherSelect.addEventListener('change', updateCipherFields);
    updateCipherFields();
}

modeRadios.forEach((radio) => {
    radio.addEventListener('change', updateSubmitText);
});

updateSubmitText();
