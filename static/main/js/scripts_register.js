
document.addEventListener('DOMContentLoaded', function() {
    // Toggle password visibility
    const passwordFields = document.querySelectorAll('.input-with-icon');
    
    passwordFields.forEach(field => {
        if (field.querySelector('input[type="password"]')) {
            const eyeIcon = document.createElement('i');
            eyeIcon.className = 'fas fa-eye toggle-password';
            eyeIcon.style.position = 'absolute';
            eyeIcon.style.right = '15px';
            eyeIcon.style.top = '50%';
            eyeIcon.style.transform = 'translateY(-50%)';
            eyeIcon.style.cursor = 'pointer';
            eyeIcon.style.color = '#777';
            
            eyeIcon.addEventListener('click', function() {
                const input = field.querySelector('input');
                if (input.type === 'password') {
                    input.type = 'text';
                    this.classList.replace('fa-eye', 'fa-eye-slash');
                } else {
                    input.type = 'password';
                    this.classList.replace('fa-eye-slash', 'fa-eye');
                }
            });
            
            field.appendChild(eyeIcon);
        }
    });
});
