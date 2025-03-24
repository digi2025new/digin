document.addEventListener('DOMContentLoaded', () => {
    // Example: password strength indicator for the signup page
    const passwordInput = document.getElementById('password');
    const strengthIndicator = document.getElementById('strength-indicator');
    if (passwordInput && strengthIndicator) {
      passwordInput.addEventListener('input', () => {
        const password = passwordInput.value;
        if (password.length < 6) {
          strengthIndicator.textContent = 'Weak';
          strengthIndicator.style.color = 'red';
        } else if (password.length < 10) {
          strengthIndicator.textContent = 'Moderate';
          strengthIndicator.style.color = 'orange';
        } else {
          strengthIndicator.textContent = 'Strong';
          strengthIndicator.style.color = 'green';
        }
      });
    }
  });
  