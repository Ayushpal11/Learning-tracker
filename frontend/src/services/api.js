import axios from 'axios';

// const API_URL = 'http://localhost:8000';
const API_URL = 'https://learning-tracker-xy7y.onrender.com';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    withCredentials: true
});

// Topics API
export const topicsApi = {
    getAll: () => api.get('/topics'),
    getById: (id) => api.get(`/topics/${id}`),
    create: (data) => api.post('/topics', data),
    update: (id, data) => api.put(`/topics/${id}`, data),
    delete: (id) => api.delete(`/topics/${id}`),
    updateProgress: (id, progress, timeSpent) =>
        api.put(`/topics/${id}/progress`, { progress, time_spent_minutes: timeSpent }),
};

// Resources API
export const resourcesApi = {
    add: (topicId, resource) => api.post(`/topics/${topicId}/resources`, resource),
    get: (topicId) => api.get(`/topics/${topicId}/resources`),
    update: (topicId, index, resource) =>
        api.put(`/topics/${topicId}/resources/${index}`, resource),
    delete: (topicId, index) =>
        api.delete(`/topics/${topicId}/resources/${index}`),
    markComplete: (topicId, index, completed) =>
        api.put(`/topics/${topicId}/resources/${index}/complete`, { completed }),
};

// Study Plans API
export const plansApi = {
    getAll: (params = { user_id: 'default' }) => api.get('/plan/', { params }),
    getToday: () => api.get('/plan/today'),
    generate: (data) => api.post('/plan/generate', {
        user_id: data.user_id || 'default',
        total_minutes: data.duration || 60,
        topic_ids: data.topics || [],
        prioritize_low_progress: true,
        date: new Date().toISOString()
    }),
    markSessionComplete: (planId, sessionIndex, completed) =>
        api.put('/plan/mark-complete', {
            plan_id: planId,
            session_index: sessionIndex,
            completed
        }),
    markActivityComplete: (planId, activityIndex, completed) =>
        api.put('/plan/mark-activity-complete', {
            plan_id: planId,
            activity_index: activityIndex,
            completed
        }),
    deletePlan: async (planId) => {
        return await axios.delete(`${API_URL}/plan/${planId}`);
    },
    addToGoogleCalendar: async (planId, email) => {
        return await axios.post(`${API_URL}/plan/${planId}/calendar`, { email });
    }
};

// Quizzes API
export const quizzesApi = {
    generate: (data) =>
        api.post('/quizzes/generate', {
            topic_id: data.topic_id,
            num_questions: data.num_questions,
            title: data.title,
            difficulty: data.difficulty,
        }),
    getById: (id) => api.get(`/quizzes/${id}`),
    getByTopic: (topicId) => api.get(`/quizzes/topic/${topicId}/quizzes`),
    take: (quizId, answers) =>
        api.post(`/quizzes/${quizId}/take`, answers),  // Send answers array directly
    getAll: (params) => api.get('/quizzes', { params }),
    delete: (id) => api.delete(`/quizzes/${id}`),
};

// Analytics API
export const analyticsApi = {
    getProgress: (userId) => api.get('/analytics/progress', { params: { user_id: userId } }),
    getTopicStats: () => api.get('/analytics/topic-stats'),
    getStreak: (userId) => api.get('/analytics/streak', { params: { user_id: userId } }),
    getTimeDistribution: () => api.get('/analytics/time-distribution'),
    getRecommendations: () => api.get('/analytics/recommendations'),
};

export default api; 