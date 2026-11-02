document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('obs-textarea');
    const countSpan = document.getElementById('char-count');
    
    if (textarea && countSpan) {
        textarea.addEventListener('input', function() {
            countSpan.textContent = this.value.length;
        });
    }
});