document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        const flashes = document.querySelectorAll('.flash-message');
        flashes.forEach(flash => flash.remove());
    }, 3000);
});