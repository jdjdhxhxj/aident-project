/**
 * StudyMind Authentication Handlers
 * Add this to your registration.html or index.html
 * Replace your existing handleLogin and handleRegister functions
 */

// API Base URL - change this if your server runs on different port
const API_URL = '/api';

/**
 * Handle Login Form Submission
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const form = event.target;
    const email = form.querySelector('input[type="email"]').value.trim();
    const password = form.querySelector('input[type="password"]').value;
    const rememberMe = form.querySelector('#remember-me')?.checked || false;
    
    // Validate inputs
    if (!email || !password) {
        showError('Please enter both email and password');
        return;
    }
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = 'Signing in...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password, rememberMe })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Login successful - save user info and redirect
            localStorage.setItem('studymind_user', JSON.stringify(data.user));
            showSuccess('Login successful! Redirecting...');
            
            setTimeout(() => {
                window.location.href = 'menu.html';
            }, 500);
        } else {
            // Login failed - show error message
            showError(data.error || 'Login failed. Please try again.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('Cannot connect to server. Please make sure the server is running.');
    } finally {
        // Restore button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

/**
 * Handle Registration Form Submission
 */
async function handleRegister(event) {
    event.preventDefault();
    
    const form = event.target;
    const firstName = form.querySelector('input[placeholder="John"]')?.value.trim() 
                   || form.querySelector('input[name="firstName"]')?.value.trim();
    const lastName = form.querySelector('input[placeholder="Doe"]')?.value.trim()
                  || form.querySelector('input[name="lastName"]')?.value.trim();
    const email = form.querySelector('input[type="email"]').value.trim();
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm').value;
    const termsAccepted = form.querySelector('#terms')?.checked;
    
    // Validate inputs
    if (!firstName || !lastName) {
        showError('Please enter your first and last name');
        return;
    }
    
    if (!email) {
        showError('Please enter your email');
        return;
    }
    
    if (!email.includes('@') || !email.includes('.')) {
        showError('Please enter a valid email address');
        return;
    }
    
    if (!password) {
        showError('Please enter a password');
        return;
    }
    
    if (password.length < 6) {
        showError('Password must be at least 6 characters');
        return;
    }
    
    if (password !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }
    
    if (!termsAccepted) {
        showError('Please accept the Terms of Service');
        return;
    }
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = 'Creating account...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                email, 
                password, 
                firstName, 
                lastName 
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Registration successful
            localStorage.setItem('studymind_user', JSON.stringify(data.user));
            showSuccess('Account created! Redirecting...');
            
            setTimeout(() => {
                window.location.href = 'menu.html';
            }, 500);
        } else {
            // Registration failed - show error
            showError(data.error || 'Registration failed. Please try again.');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showError('Cannot connect to server. Please make sure the server is running.');
    } finally {
        // Restore button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

/**
 * Check if user is already logged in
 */
async function checkAuth() {
    try {
        const response = await fetch(`${API_URL}/auth/check`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.authenticated) {
            // User is already logged in
            localStorage.setItem('studymind_user', JSON.stringify(data.user));
            return data.user;
        }
    } catch (error) {
        console.log('Not authenticated');
    }
    return null;
}

/**
 * Logout user
 */
async function handleLogout() {
    try {
        await fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    // Clear local storage and redirect
    localStorage.removeItem('studymind_user');
    window.location.href = 'index.html';
}

/**
 * Show error message to user
 */
function showError(message) {
    // Remove any existing error messages
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create error element
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
        background: rgba(229, 115, 115, 0.2);
        border: 1px solid #e57373;
        color: #e57373;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 16px;
        font-size: 14px;
        text-align: center;
        animation: fadeIn 0.3s ease;
    `;
    errorDiv.textContent = message;
    
    // Insert before the form or at the top of form-content
    const formContent = document.querySelector('.form-content form') 
                     || document.querySelector('.form-content');
    if (formContent) {
        formContent.insertBefore(errorDiv, formContent.firstChild);
    }
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

/**
 * Show success message to user
 */
function showSuccess(message) {
    // Remove any existing messages
    const existingMsg = document.querySelector('.success-message, .error-message');
    if (existingMsg) {
        existingMsg.remove();
    }
    
    // Create success element
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.style.cssText = `
        background: rgba(129, 199, 132, 0.2);
        border: 1px solid #81c784;
        color: #81c784;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 16px;
        font-size: 14px;
        text-align: center;
        animation: fadeIn 0.3s ease;
    `;
    successDiv.textContent = message;
    
    // Insert before the form
    const formContent = document.querySelector('.form-content form') 
                     || document.querySelector('.form-content');
    if (formContent) {
        formContent.insertBefore(successDiv, formContent.firstChild);
    }
}

/**
 * Load user data on menu.html (dashboard)
 */
async function loadDashboard() {
    // Check if user is logged in
    const user = JSON.parse(localStorage.getItem('studymind_user'));
    
    if (!user) {
        // Not logged in - redirect to login
        window.location.href = 'index.html';
        return;
    }
    
    // Update UI with user info
    const userNameEl = document.querySelector('.user-name');
    const userAvatarEl = document.querySelector('.user-avatar');
    
    if (userNameEl) {
        userNameEl.textContent = user.full_name || `${user.first_name} ${user.last_name}`;
    }
    
    if (userAvatarEl) {
        userAvatarEl.textContent = user.avatar_initials || 
            `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase();
    }
    
    // Load stats from API
    try {
        const response = await fetch(`${API_URL}/user/stats`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const stats = await response.json();
            updateDashboardStats(stats);
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

/**
 * Update dashboard statistics
 */
function updateDashboardStats(stats) {
    // Update stat cards (if they exist)
    const statValues = document.querySelectorAll('.stat-value');
    
    if (statValues.length >= 4) {
        statValues[0].textContent = `${stats.studyTime?.value || 0}${stats.studyTime?.unit || 'h'}`;
        statValues[1].textContent = stats.materials?.value || 0;
        statValues[2].textContent = stats.tasks?.value || '0/0';
        statValues[3].textContent = stats.streak?.value || 0;
    }
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);
