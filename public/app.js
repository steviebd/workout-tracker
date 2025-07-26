// Workout Tracker PWA - Main Application
class WorkoutTracker {
    constructor() {
        this.apiBase = '/api';
        this.token = localStorage.getItem('token');
        this.currentUser = null;
        this.currentTemplate = null;
        this.currentSession = null;
        this.isOnline = navigator.onLine;
        
        this.initializeIndexedDB();
        this.registerServiceWorker();
        this.setupEventListeners();
        this.checkAuthentication();
        this.setupOfflineHandling();
    }

    // IndexedDB Setup
    initializeIndexedDB() {
        this.db = new Dexie('WorkoutTracker');
        this.db.version(1).stores({
            templates: '++id, user_id, name, exercises',
            sessions: '++id, user_id, template_id, session_date, exercises, synced',
            pendingRequests: '++id, method, url, body, timestamp'
        });
    }

    // Service Worker Registration
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('SW registered:', registration);
                
                // Listen for messages from service worker
                navigator.serviceWorker.addEventListener('message', (event) => {
                    if (event.data.type === 'SYNC_DATA') {
                        this.syncOfflineData();
                    }
                });
            } catch (error) {
                console.error('SW registration failed:', error);
            }
        }
    }

    // Event Listeners
    setupEventListeners() {
        // Auth events
        document.getElementById('login-btn').addEventListener('click', () => this.login());
        document.getElementById('logout-btn').addEventListener('click', () => this.logout());

        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Templates
        document.getElementById('add-template-btn').addEventListener('click', () => this.showTemplateModal());
        document.getElementById('close-modal-btn').addEventListener('click', () => this.hideTemplateModal());
        document.getElementById('save-template-btn').addEventListener('click', () => this.saveTemplate());
        document.getElementById('cancel-template-btn').addEventListener('click', () => this.hideTemplateModal());
        document.getElementById('add-exercise-btn').addEventListener('click', () => this.addExerciseInput());

        // Workout
        document.getElementById('workout-template-select').addEventListener('change', (e) => {
            document.getElementById('start-workout-btn').disabled = !e.target.value;
        });
        document.getElementById('start-workout-btn').addEventListener('click', () => this.startWorkout());
        document.getElementById('save-session-btn').addEventListener('click', () => this.saveSession());
        document.getElementById('cancel-session-btn').addEventListener('click', () => this.cancelSession());

        // History filter
        document.getElementById('history-filter').addEventListener('change', (e) => this.loadHistory(e.target.value));

        // Enter key handlers
        document.getElementById('password').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.login();
        });
    }

    // Offline Handling
    setupOfflineHandling() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.hideOfflineBanner();
            this.syncOfflineData();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showOfflineBanner();
        });

        // Update banner on load
        if (!this.isOnline) {
            this.showOfflineBanner();
        }
    }

    showOfflineBanner() {
        document.getElementById('offline-banner').classList.remove('hidden');
    }

    hideOfflineBanner() {
        document.getElementById('offline-banner').classList.add('hidden');
    }

    // Authentication
    async checkAuthentication() {
        if (this.token) {
            try {
                // Try to fetch templates to verify token
                await this.apiCall('GET', '/templates');
                this.showMainScreen();
                this.loadTemplates();
            } catch (error) {
                this.token = null;
                localStorage.removeItem('token');
                this.showAuthScreen();
            }
        } else {
            this.showAuthScreen();
        }
        this.hideLoadingScreen();
    }

    async login() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        if (!username || !password) {
            alert('Please enter username and password');
            return;
        }

        try {
            const response = await this.apiCall('POST', '/auth/login', { username, password });
            this.token = response.access_token;
            this.currentUser = response.user_id;
            localStorage.setItem('token', this.token);
            
            this.showMainScreen();
            this.loadTemplates();
        } catch (error) {
            alert('Login failed: ' + error.message);
        }
    }



    logout() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('token');
        this.showAuthScreen();
    }

    // Screen Management
    showLoadingScreen() {
        document.getElementById('loading-screen').classList.remove('hidden');
        document.getElementById('auth-screen').classList.add('hidden');
        document.getElementById('main-screen').classList.add('hidden');
    }

    hideLoadingScreen() {
        document.getElementById('loading-screen').classList.add('hidden');
    }

    showAuthScreen() {
        document.getElementById('auth-screen').classList.remove('hidden');
        document.getElementById('main-screen').classList.add('hidden');
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
    }

    showMainScreen() {
        document.getElementById('auth-screen').classList.add('hidden');
        document.getElementById('main-screen').classList.remove('hidden');
    }

    // Navigation
    switchTab(tabName) {
        // Update nav buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('border-blue-500', 'text-blue-600');
            btn.classList.add('border-transparent', 'text-gray-500');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.remove('border-transparent', 'text-gray-500');
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('border-blue-500', 'text-blue-600');

        // Show/hide content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        document.getElementById(`${tabName}-tab`).classList.remove('hidden');

        // Load content based on tab
        if (tabName === 'templates') {
            this.loadTemplates();
        } else if (tabName === 'workout') {
            this.loadWorkoutTemplates();
        } else if (tabName === 'history') {
            this.loadHistory();
        }
    }

    // API Calls
    async apiCall(method, endpoint, body = null) {
        const url = this.apiBase + endpoint;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (body) {
            options.body = JSON.stringify(body);
        }

        if (!this.isOnline && ['POST', 'PUT', 'DELETE'].includes(method)) {
            // Store for offline sync
            await this.db.pendingRequests.add({
                method,
                url,
                body: options.body,
                timestamp: new Date().toISOString()
            });
            throw new Error('Request saved for offline sync');
        }

        const response = await fetch(url, options);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Request failed');
        }

        return response.json();
    }

    // Offline Sync
    async syncOfflineData() {
        if (!this.isOnline) return;

        try {
            const pendingRequests = await this.db.pendingRequests.toArray();
            
            for (const request of pendingRequests) {
                try {
                    const options = {
                        method: request.method,
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${this.token}`
                        }
                    };

                    if (request.body) {
                        options.body = request.body;
                    }

                    await fetch(request.url, options);
                    await this.db.pendingRequests.delete(request.id);
                } catch (error) {
                    console.error('Failed to sync request:', error);
                }
            }

            // Reload current data
            this.loadTemplates();
            this.loadHistory();
        } catch (error) {
            console.error('Sync failed:', error);
        }
    }

    // Templates Management
    async loadTemplates() {
        try {
            const templates = await this.apiCall('GET', '/templates');
            this.renderTemplates(templates);
        } catch (error) {
            // Load from IndexedDB if offline
            const templates = await this.db.templates.where('user_id').equals(this.currentUser).toArray();
            this.renderTemplates(templates);
        }
    }

    renderTemplates(templates) {
        const container = document.getElementById('templates-list');
        
        if (templates.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-8">No templates yet. Create your first template!</p>';
            return;
        }

        container.innerHTML = templates.map(template => `
            <div class="bg-white border border-gray-200 rounded-lg p-4">
                <div class="flex items-center justify-between">
                    <h3 class="font-medium text-gray-800">${template.name}</h3>
                    <div class="flex space-x-2">
                        <button class="text-blue-500 text-sm hover:text-blue-600" onclick="app.editTemplate(${template.id})">
                            Edit
                        </button>
                        <button class="text-red-500 text-sm hover:text-red-600" onclick="app.deleteTemplate(${template.id})">
                            Delete
                        </button>
                    </div>
                </div>
                <div class="mt-2" id="template-exercises-${template.id}">
                    <div class="text-sm text-gray-600">Loading exercises...</div>
                </div>
            </div>
        `).join('');

        // Load exercises for each template
        templates.forEach(template => this.loadTemplateExercises(template.id));
    }

    async loadTemplateExercises(templateId) {
        try {
            const exercises = await this.apiCall('GET', `/templates/${templateId}/exercises`);
            const container = document.getElementById(`template-exercises-${templateId}`);
            
            if (exercises.length === 0) {
                container.innerHTML = '<div class="text-sm text-gray-500">No exercises</div>';
            } else {
                container.innerHTML = exercises.map(ex => `
                    <span class="inline-block bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded mr-1 mb-1">
                        ${ex.name}
                    </span>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load exercises:', error);
        }
    }

    showTemplateModal(template = null) {
        this.currentTemplate = template;
        document.getElementById('modal-title').textContent = template ? 'Edit Template' : 'Add Template';
        document.getElementById('template-name').value = template ? template.name : '';
        
        // Clear exercises
        document.getElementById('exercises-inputs').innerHTML = '';
        
        if (template) {
            this.loadTemplateForEdit(template.id);
        } else {
            this.addExerciseInput();
        }
        
        document.getElementById('template-modal').classList.remove('hidden');
    }

    async loadTemplateForEdit(templateId) {
        try {
            const exercises = await this.apiCall('GET', `/templates/${templateId}/exercises`);
            exercises.forEach(exercise => {
                this.addExerciseInput(exercise.name);
            });
        } catch (error) {
            console.error('Failed to load template for edit:', error);
        }
    }

    hideTemplateModal() {
        document.getElementById('template-modal').classList.add('hidden');
        this.currentTemplate = null;
    }

    addExerciseInput(value = '') {
        const container = document.getElementById('exercises-inputs');
        const exerciseDiv = document.createElement('div');
        exerciseDiv.className = 'flex items-center space-x-2';
        exerciseDiv.innerHTML = `
            <input type="text" class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm" 
                   placeholder="Exercise name" value="${value}">
            <button type="button" class="text-red-500 hover:text-red-600" onclick="this.parentElement.remove()">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;
        container.appendChild(exerciseDiv);
    }

    async saveTemplate() {
        const name = document.getElementById('template-name').value.trim();
        if (!name) {
            alert('Please enter a template name');
            return;
        }

        const exerciseInputs = document.querySelectorAll('#exercises-inputs input');
        const exercises = Array.from(exerciseInputs)
            .map(input => input.value.trim())
            .filter(name => name);

        if (exercises.length === 0) {
            alert('Please add at least one exercise');
            return;
        }

        try {
            if (this.currentTemplate) {
                await this.apiCall('PUT', `/templates/${this.currentTemplate.id}`, { name, exercises });
            } else {
                await this.apiCall('POST', '/templates', { name, exercises });
            }
            
            this.hideTemplateModal();
            this.loadTemplates();
        } catch (error) {
            if (!this.isOnline) {
                // Save to IndexedDB for offline
                await this.db.templates.add({
                    user_id: this.currentUser,
                    name,
                    exercises,
                    synced: false
                });
                this.hideTemplateModal();
                this.loadTemplates();
            } else {
                alert('Failed to save template: ' + error.message);
            }
        }
    }

    async editTemplate(templateId) {
        try {
            const template = await this.apiCall('GET', `/templates`);
            const templateToEdit = template.find(t => t.id === templateId);
            this.showTemplateModal(templateToEdit);
        } catch (error) {
            console.error('Failed to load template for edit:', error);
        }
    }

    async deleteTemplate(templateId) {
        if (!confirm('Are you sure you want to delete this template?')) return;

        try {
            await this.apiCall('DELETE', `/templates/${templateId}`);
            this.loadTemplates();
        } catch (error) {
            alert('Failed to delete template: ' + error.message);
        }
    }

    // Workout Session
    async loadWorkoutTemplates() {
        try {
            const templates = await this.apiCall('GET', '/templates');
            const select = document.getElementById('workout-template-select');
            
            select.innerHTML = '<option value="">Select a template...</option>';
            templates.forEach(template => {
                select.innerHTML += `<option value="${template.id}">${template.name}</option>`;
            });
        } catch (error) {
            console.error('Failed to load workout templates:', error);
        }
    }

    async startWorkout() {
        const templateId = parseInt(document.getElementById('workout-template-select').value);
        if (!templateId) return;

        try {
            const templates = await this.apiCall('GET', '/templates');
            const template = templates.find(t => t.id === templateId);
            const exercises = await this.apiCall('GET', `/templates/${templateId}/exercises`);

            this.currentSession = {
                template_id: templateId,
                template_name: template.name,
                start_time: new Date().toISOString(),
                exercises: []
            };

            // Hide template selection, show workout session
            document.getElementById('template-selection').classList.add('hidden');
            document.getElementById('workout-session').classList.remove('hidden');

            // Update session info
            document.getElementById('session-time').textContent = new Date().toLocaleString();
            document.getElementById('session-template').textContent = template.name;

            // Load exercises with last values
            await this.loadWorkoutExercises(exercises);

        } catch (error) {
            alert('Failed to start workout: ' + error.message);
        }
    }

    async loadWorkoutExercises(exercises) {
        const container = document.getElementById('exercises-list');
        container.innerHTML = '';

        for (const exercise of exercises) {
            // Get last values
            let lastValues = { weight_kg: '', reps: '', sets: '' };
            try {
                const latest = await this.apiCall('GET', `/sessions/latest/${exercise.id}`);
                if (latest.weight_kg !== undefined) {
                    lastValues = latest;
                }
            } catch (error) {
                console.log('No previous data for exercise:', exercise.name);
            }

            const exerciseDiv = document.createElement('div');
            exerciseDiv.className = 'bg-gray-50 p-4 rounded-lg';
            exerciseDiv.innerHTML = `
                <div class="flex items-center justify-between mb-3">
                    <h4 class="font-medium text-gray-800">${exercise.name}</h4>
                    <label class="flex items-center space-x-2">
                        <input type="checkbox" class="checkbox-done" data-exercise-id="${exercise.id}">
                        <span class="text-sm text-gray-600">Done</span>
                    </label>
                </div>
                <div class="grid grid-cols-3 gap-2">
                    <div>
                        <label class="block text-xs text-gray-600 mb-1">Weight (kg)</label>
                        <input type="number" step="0.5" class="w-full px-2 py-1 border border-gray-300 rounded text-sm" 
                               value="${lastValues.weight_kg}" data-field="weight" data-exercise-id="${exercise.id}">
                    </div>
                    <div>
                        <label class="block text-xs text-gray-600 mb-1">Reps</label>
                        <input type="number" class="w-full px-2 py-1 border border-gray-300 rounded text-sm" 
                               value="${lastValues.reps}" data-field="reps" data-exercise-id="${exercise.id}">
                    </div>
                    <div>
                        <label class="block text-xs text-gray-600 mb-1">Sets</label>
                        <input type="number" class="w-full px-2 py-1 border border-gray-300 rounded text-sm" 
                               value="${lastValues.sets}" data-field="sets" data-exercise-id="${exercise.id}">
                    </div>
                </div>
            `;
            container.appendChild(exerciseDiv);
        }
    }

    async saveSession() {
        const exerciseInputs = document.querySelectorAll('#exercises-list input[type="number"]');
        const exercises = [];

        // Group inputs by exercise ID
        const exerciseData = {};
        exerciseInputs.forEach(input => {
            const exerciseId = input.dataset.exerciseId;
            const field = input.dataset.field;
            
            if (!exerciseData[exerciseId]) {
                exerciseData[exerciseId] = { template_exercise_id: parseInt(exerciseId) };
            }
            
            exerciseData[exerciseId][field + '_kg'] = field === 'weight' ? parseFloat(input.value) || 0 : undefined;
            if (field !== 'weight') {
                exerciseData[exerciseId][field] = parseInt(input.value) || 0;
            }
        });

        // Clean up data and only include completed exercises
        Object.values(exerciseData).forEach(data => {
            if (data.weight_kg !== undefined) {
                const exerciseInput = {
                    template_exercise_id: data.template_exercise_id,
                    weight_kg: data.weight_kg,
                    reps: data.reps || 0,
                    sets: data.sets || 0
                };
                exercises.push(exerciseInput);
            }
        });

        if (exercises.length === 0) {
            alert('Please enter data for at least one exercise');
            return;
        }

        try {
            const sessionData = {
                template_id: this.currentSession.template_id,
                session_date: this.currentSession.start_time,
                exercises
            };

            await this.apiCall('POST', '/sessions', sessionData);
            alert('Session saved successfully!');
            this.cancelSession();
        } catch (error) {
            if (!this.isOnline) {
                // Save to IndexedDB for offline
                await this.db.sessions.add({
                    user_id: this.currentUser,
                    template_id: this.currentSession.template_id,
                    session_date: this.currentSession.start_time,
                    exercises,
                    synced: false
                });
                alert('Session saved offline - will sync when online');
                this.cancelSession();
            } else {
                alert('Failed to save session: ' + error.message);
            }
        }
    }

    cancelSession() {
        this.currentSession = null;
        document.getElementById('template-selection').classList.remove('hidden');
        document.getElementById('workout-session').classList.add('hidden');
        document.getElementById('workout-template-select').value = '';
        document.getElementById('start-workout-btn').disabled = true;
    }

    // History
    async loadHistory(templateFilter = '') {
        try {
            const url = templateFilter ? `/sessions?template=${templateFilter}` : '/sessions';
            const sessions = await this.apiCall('GET', url);
            this.renderHistory(sessions);
            this.updateHistoryFilter();
        } catch (error) {
            console.error('Failed to load history:', error);
            // Load from IndexedDB if offline
            const sessions = await this.db.sessions.where('user_id').equals(this.currentUser).toArray();
            this.renderHistory(sessions);
        }
    }

    renderHistory(sessions) {
        const container = document.getElementById('sessions-list');
        
        if (sessions.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-8">No workout sessions yet. Start your first workout!</p>';
            return;
        }

        container.innerHTML = sessions.map(session => `
            <div class="bg-white border border-gray-200 rounded-lg p-4">
                <div class="flex items-center justify-between mb-2">
                    <h3 class="font-medium text-gray-800">${session.template_name}</h3>
                    <button class="text-red-500 text-sm hover:text-red-600" onclick="app.deleteSession(${session.id})">
                        Delete
                    </button>
                </div>
                <p class="text-sm text-gray-600 mb-2">
                    📅 ${new Date(session.session_date).toLocaleDateString()} 
                    🕐 ${new Date(session.session_date).toLocaleTimeString()}
                </p>
                ${session.exercises ? `
                    <div class="space-y-1">
                        ${session.exercises.map(ex => `
                            <div class="text-sm text-gray-700">
                                <span class="font-medium">${ex.exercise_name}:</span> 
                                ${ex.weight_kg}kg × ${ex.reps} reps × ${ex.sets} sets
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    async updateHistoryFilter() {
        try {
            const templates = await this.apiCall('GET', '/templates');
            const filter = document.getElementById('history-filter');
            
            filter.innerHTML = '<option value="">All Templates</option>';
            templates.forEach(template => {
                filter.innerHTML += `<option value="${template.id}">${template.name}</option>`;
            });
        } catch (error) {
            console.error('Failed to update history filter:', error);
        }
    }

    async deleteSession(sessionId) {
        if (!confirm('Are you sure you want to delete this session?')) return;

        try {
            await this.apiCall('DELETE', `/sessions/${sessionId}`);
            this.loadHistory();
        } catch (error) {
            alert('Failed to delete session: ' + error.message);
        }
    }
}

// Initialize the app
const app = new WorkoutTracker();

// Make app globally available for onclick handlers
window.app = app;
