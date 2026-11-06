document.addEventListener('DOMContentLoaded', function() {
    let timeLeft = 50;
    const countdown = document.getElementById('countdown');
    
    const timer = setInterval(function() {
        timeLeft--;
        if (countdown) {
            countdown.textContent = timeLeft;
        }
        
        if (timeLeft <= 0) {
            clearInterval(timer);
            location.reload();
        }
    }, 1000);
});