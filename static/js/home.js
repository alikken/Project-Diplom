document.addEventListener('DOMContentLoaded', function() {
    const text = document.querySelector('.typing-animation');
    const textContent = text.textContent;
    text.textContent = '';
    text.style.opacity = '1';
    text.classList.add('typing');

    let charIndex = 0;
    const typingSpeed = 100; // Скорость печатания (мс)

    function typeText() {
        if (charIndex < textContent.length) {
            text.textContent += textContent.charAt(charIndex);
            charIndex++;
            setTimeout(typeText, typingSpeed);
        } else {
            // Анимация завершена
            text.classList.remove('typing');
            text.classList.add('typing-done');
        }
    }

    // Небольшая задержка перед началом анимации
    setTimeout(typeText, 500);
});