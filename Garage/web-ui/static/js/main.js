document.addEventListener('DOMContentLoaded', function() {
    // Input validation
    const numericInputs = document.querySelectorAll('input[type="number"]');
    
    numericInputs.forEach(input => {
        input.addEventListener('input', function() {
            if (parseFloat(this.value) <= 0) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    });
    
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    setTimeout(() => {
        flashMessages.forEach(message => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 500);
        });
    }, 5000);
});
