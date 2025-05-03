import { useState, useEffect } from 'react';
import { topicsApi } from '../services/api';
import {
    BookOpenIcon,
    ChartBarIcon,
    ClockIcon,
    CalendarIcon
} from '@heroicons/react/24/outline';

export default function Dashboard() {
    const [topics, setTopics] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchTopics();
    }, []);

    const fetchTopics = async () => {
        try {
            const response = await topicsApi.getAll();
            if (response.data && response.data.data && response.data.data.topics) {
                setTopics(response.data.data.topics);
            } else {
                console.warn('Unexpected response format:', response.data);
                setTopics([]);
            }
            setLoading(false);
        } catch (err) {
            console.error('Error fetching topics:', err);
            setError('Failed to load topics');
            setLoading(false);
            setTopics([]);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="text-red-500">{error}</div>
            </div>
        );
    }

    // Calculate dashboard statistics
    const totalTopics = topics.length;
    const completedTopics = topics.filter(topic => topic.progress >= 100).length;
    const inProgressTopics = topics.filter(topic => topic.progress > 0 && topic.progress < 100).length;
    const notStartedTopics = topics.filter(topic => topic.progress === 0).length;
    const totalTimeSpent = topics.reduce((sum, topic) => sum + (topic.time_spent_minutes || 0), 0);

    return (
        <div className="space-y-8 p-8 bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-primary-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Total Topics</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">{totalTopics}</p>
                        </div>
                        <div className="p-3 bg-primary-50 rounded-full">
                            <BookOpenIcon className="h-6 w-6 text-primary-600" />
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-green-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Completed Topics</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">{completedTopics}</p>
                        </div>
                        <div className="p-3 bg-green-50 rounded-full">
                            <ChartBarIcon className="h-6 w-6 text-green-600" />
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-blue-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-500">In Progress</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">{inProgressTopics}</p>
                        </div>
                        <div className="p-3 bg-blue-50 rounded-full">
                            <ClockIcon className="h-6 w-6 text-blue-600" />
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-purple-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Total Time Spent</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">
                                {Math.floor(totalTimeSpent / 60)}h {totalTimeSpent % 60}m
                            </p>
                        </div>
                        <div className="p-3 bg-purple-50 rounded-full">
                            <CalendarIcon className="h-6 w-6 text-purple-600" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Topics */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Topics</h2>
                <div className="space-y-4">
                    {topics
                        .sort((a, b) => new Date(b.last_studied || 0) - new Date(a.last_studied || 0))
                        .slice(0, 5)
                        .map((topic) => (
                            <div key={topic._id} className="flex items-center justify-between p-4 rounded-xl hover:bg-gray-50">
                                <div className="flex items-center space-x-4">
                                    <div className="p-2 bg-primary-50 rounded-full">
                                        <BookOpenIcon className="h-5 w-5 text-primary-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-gray-900">{topic.title}</p>
                                        <p className="text-xs text-gray-500">
                                            {topic.last_studied ? new Date(topic.last_studied).toLocaleDateString() : 'Not studied yet'}
                                        </p>
                                    </div>
                                </div>
                                <div className="text-sm font-medium text-primary-600">
                                    {topic.progress}%
                                </div>
                            </div>
                        ))}
                </div>
            </div>
        </div>
    );
} 