/**
 * StudyMind API Client
 * JavaScript client for connecting frontend to Python backend
 * Include this file in your HTML pages
 */

const StudyMindAPI = {
    // Base URL - update this to your server address
    baseURL: '/api',
    
    // ==================== CONFIGURATION ====================
    
    /**
     * Set the base URL for the API
     * @param {string} url - The base URL of your backend server
     */
    setBaseURL(url) {
        this.baseURL = url.replace(/\/$/, '') + '/api';
    },
    
    /**
     * Make an API request
     * @private
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const defaultOptions = {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ error: 'Request failed' }));
            throw new Error(error.error || `HTTP ${response.status}`);
        }
        
        return response.json();
    },
    
    // ==================== AUTHENTICATION ====================
    
    auth: {
        /**
         * Register a new user
         * @param {Object} userData - User registration data
         * @param {string} userData.email - User's email
         * @param {string} userData.password - User's password
         * @param {string} userData.firstName - User's first name
         * @param {string} userData.lastName - User's last name
         */
        async register(userData) {
            return StudyMindAPI.request('/auth/register', {
                method: 'POST',
                body: JSON.stringify(userData),
            });
        },
        
        /**
         * Login user
         * @param {string} email - User's email
         * @param {string} password - User's password
         * @param {boolean} rememberMe - Whether to remember the session
         */
        async login(email, password, rememberMe = false) {
            return StudyMindAPI.request('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password, rememberMe }),
            });
        },
        
        /**
         * Logout current user
         */
        async logout() {
            return StudyMindAPI.request('/auth/logout', {
                method: 'POST',
            });
        },
        
        /**
         * Get current user info
         */
        async me() {
            return StudyMindAPI.request('/auth/me');
        },
    },
    
    // ==================== USER ====================
    
    user: {
        /**
         * Get user statistics for dashboard
         */
        async getStats() {
            return StudyMindAPI.request('/user/stats');
        },
        
        /**
         * Get user settings
         */
        async getSettings() {
            return StudyMindAPI.request('/user/settings');
        },
        
        /**
         * Update user settings
         * @param {Object} settings - Settings to update
         */
        async updateSettings(settings) {
            return StudyMindAPI.request('/user/settings', {
                method: 'PUT',
                body: JSON.stringify(settings),
            });
        },
    },
    
    // ==================== MATERIALS ====================
    
    materials: {
        /**
         * Get all materials
         * @param {Object} filters - Optional filters
         * @param {string} filters.status - Filter by status
         * @param {string} filters.type - Filter by file type
         * @param {number} filters.limit - Max number of results
         */
        async getAll(filters = {}) {
            const params = new URLSearchParams(filters);
            return StudyMindAPI.request(`/materials?${params}`);
        },
        
        /**
         * Get a specific material
         * @param {number} id - Material ID
         */
        async get(id) {
            return StudyMindAPI.request(`/materials/${id}`);
        },
        
        /**
         * Upload a new material
         * @param {File} file - File to upload
         * @param {Object} metadata - Optional metadata
         * @param {string} metadata.name - Display name
         * @param {string} metadata.subject - Subject category
         * @param {string} metadata.tags - Comma-separated tags
         */
        async upload(file, metadata = {}) {
            const formData = new FormData();
            formData.append('file', file);
            
            if (metadata.name) formData.append('name', metadata.name);
            if (metadata.subject) formData.append('subject', metadata.subject);
            if (metadata.tags) formData.append('tags', metadata.tags);
            
            const response = await fetch(`${StudyMindAPI.baseURL}/materials`, {
                method: 'POST',
                credentials: 'include',
                body: formData,
            });
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({ error: 'Upload failed' }));
                throw new Error(error.error || 'Upload failed');
            }
            
            return response.json();
        },
        
        /**
         * Update a material
         * @param {number} id - Material ID
         * @param {Object} data - Data to update
         */
        async update(id, data) {
            return StudyMindAPI.request(`/materials/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },
        
        /**
         * Delete a material
         * @param {number} id - Material ID
         */
        async delete(id) {
            return StudyMindAPI.request(`/materials/${id}`, {
                method: 'DELETE',
            });
        },
    },
    
    // ==================== TASKS ====================
    
    tasks: {
        /**
         * Get all tasks
         * @param {Object} filters - Optional filters
         * @param {boolean} filters.completed - Filter by completion status
         * @param {number} filters.limit - Max number of results
         */
        async getAll(filters = {}) {
            const params = new URLSearchParams();
            if (filters.completed !== undefined) params.append('completed', filters.completed);
            if (filters.limit) params.append('limit', filters.limit);
            return StudyMindAPI.request(`/tasks?${params}`);
        },
        
        /**
         * Get a specific task
         * @param {number} id - Task ID
         */
        async get(id) {
            return StudyMindAPI.request(`/tasks/${id}`);
        },
        
        /**
         * Create a new task
         * @param {Object} taskData - Task data
         * @param {string} taskData.title - Task title
         * @param {string} taskData.description - Task description
         * @param {string} taskData.taskType - Type of task
         * @param {string} taskData.dueDate - Due date (ISO format)
         * @param {number} taskData.estimatedTime - Estimated time in minutes
         * @param {string} taskData.priority - Priority (low, medium, high)
         */
        async create(taskData) {
            return StudyMindAPI.request('/tasks', {
                method: 'POST',
                body: JSON.stringify(taskData),
            });
        },
        
        /**
         * Update a task
         * @param {number} id - Task ID
         * @param {Object} data - Data to update
         */
        async update(id, data) {
            return StudyMindAPI.request(`/tasks/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },
        
        /**
         * Toggle task completion
         * @param {number} id - Task ID
         */
        async toggle(id) {
            return StudyMindAPI.request(`/tasks/${id}/toggle`, {
                method: 'POST',
            });
        },
        
        /**
         * Delete a task
         * @param {number} id - Task ID
         */
        async delete(id) {
            return StudyMindAPI.request(`/tasks/${id}`, {
                method: 'DELETE',
            });
        },
    },
    
    // ==================== STUDY SESSIONS ====================
    
    sessions: {
        /**
         * Get study sessions
         * @param {number} days - Number of days to look back
         */
        async getAll(days = 7) {
            return StudyMindAPI.request(`/sessions?days=${days}`);
        },
        
        /**
         * Start a new study session
         * @param {Object} data - Session data
         * @param {number} data.materialId - Optional material ID
         * @param {string} data.activityType - Type of activity
         */
        async start(data = {}) {
            return StudyMindAPI.request('/sessions', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },
        
        /**
         * End a study session
         * @param {number} id - Session ID
         * @param {Object} data - End session data
         * @param {number} data.duration - Duration in minutes
         * @param {number} data.pagesCovered - Number of pages covered
         */
        async end(id, data) {
            return StudyMindAPI.request(`/sessions/${id}/end`, {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },
    },
    
    // ==================== NOTIFICATIONS ====================
    
    notifications: {
        /**
         * Get notifications
         * @param {Object} options - Options
         * @param {number} options.limit - Max number of results
         * @param {boolean} options.unread - Only get unread notifications
         */
        async getAll(options = {}) {
            const params = new URLSearchParams();
            if (options.limit) params.append('limit', options.limit);
            if (options.unread) params.append('unread', 'true');
            return StudyMindAPI.request(`/notifications?${params}`);
        },
        
        /**
         * Mark a notification as read
         * @param {number} id - Notification ID
         */
        async markRead(id) {
            return StudyMindAPI.request(`/notifications/${id}/read`, {
                method: 'POST',
            });
        },
        
        /**
         * Mark all notifications as read
         */
        async markAllRead() {
            return StudyMindAPI.request('/notifications/read-all', {
                method: 'POST',
            });
        },
    },
    
    // ==================== PROGRESS ====================
    
    progress: {
        /**
         * Get daily progress
         * @param {number} days - Number of days to look back
         */
        async getDaily(days = 7) {
            return StudyMindAPI.request(`/progress/daily?days=${days}`);
        },
        
        /**
         * Get weekly summary
         */
        async getWeekly() {
            return StudyMindAPI.request('/progress/weekly');
        },
    },
};


// ==================== USAGE EXAMPLES ====================

/*
// Set your backend URL (if different from localhost:5000)
StudyMindAPI.setBaseURL('https://your-server.com');

// Register a new user
try {
    const result = await StudyMindAPI.auth.register({
        email: 'user@example.com',
        password: 'securepassword',
        firstName: 'John',
        lastName: 'Doe'
    });
    console.log('Registered:', result.user);
} catch (error) {
    console.error('Registration failed:', error.message);
}

// Login
try {
    const result = await StudyMindAPI.auth.login('user@example.com', 'securepassword', true);
    console.log('Logged in:', result.user);
} catch (error) {
    console.error('Login failed:', error.message);
}

// Get dashboard stats
const stats = await StudyMindAPI.user.getStats();
console.log('Stats:', stats);

// Upload a file
const fileInput = document.querySelector('#fileInput');
const file = fileInput.files[0];
const material = await StudyMindAPI.materials.upload(file, {
    name: 'My Study Notes',
    subject: 'Mathematics'
});
console.log('Uploaded:', material);

// Create a task
const task = await StudyMindAPI.tasks.create({
    title: 'Review Chapter 5',
    taskType: 'review',
    dueDate: '2026-01-15T10:00:00Z',
    estimatedTime: 30,
    priority: 'high'
});
console.log('Created task:', task);

// Start a study session
const session = await StudyMindAPI.sessions.start({
    materialId: material.id,
    activityType: 'reading'
});

// End the session after studying
await StudyMindAPI.sessions.end(session.id, {
    duration: 45,
    pagesCovered: 12
});

// Get notifications
const { notifications, unread_count } = await StudyMindAPI.notifications.getAll({ limit: 10 });
console.log(`You have ${unread_count} unread notifications`);
*/


// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StudyMindAPI;
}
