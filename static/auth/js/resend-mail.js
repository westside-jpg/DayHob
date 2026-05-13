const text = document.querySelector('.resend-text');
const button = document.querySelector('.resend-btn');

let seconds = 60;
let timer = null;

function getSecondsWord(n) {
    const remainder10 = n % 10;
    const remainder100 = n % 100;

    if (remainder100 >= 11 && remainder100 <= 19) {
        return 'секунд';
    }
    if (remainder10 === 1) {
        return 'секунда';
    }
    if (remainder10 >= 2 && remainder10 <= 4) {
        return 'секунды';
    }
    return 'секунд';
}

function startTimer() {
    clearInterval(timer);
    timer = setInterval(() => {
        if (seconds > 0) {
            const word = getSecondsWord(seconds);
            text.textContent = `До повторной отправки письма ${seconds} ${word}...`;
            text.style.display = 'block';
            button.style.display = 'none';
            seconds--;
        } else {
            text.style.display = "none";
            button.style.display = "block";
            clearInterval(timer);
        }
    }, 1000);
}

startTimer();

const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('resent') === 'true') {

    const email = urlParams.get('email');
    window.history.replaceState({}, '', window.location.pathname + '?email=' + email);

    seconds = 60;
    startTimer();
}