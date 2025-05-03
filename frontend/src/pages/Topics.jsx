import { useState, useEffect } from 'react';
import { topicsApi } from '../services/api';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

export default function Topics() {
    const [topics, setTopics] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [newTopic, setNewTopic] = useState({
        title: '',
        description: '',
        difficulty: 'beginner',
        tags: []
    });

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
        } catch (error) {
            console.error('Error fetching topics:', error);
            toast.error('Failed to fetch topics');
            setLoading(false);
            setTopics([]);
        }
    };

    const handleAddTopic = async (e) => {
        e.preventDefault();
        try {
            // Format the data according to the TopicCreate model
            const topicData = {
                title: newTopic.title,
                description: newTopic.description,
                tags: newTopic.tags,
                priority: 1, // Default priority
                progress: 0, // Initial progress
                time_spent_minutes: 0 // Initial time spent
            };

            const response = await topicsApi.create(topicData);
            if (response.data && response.data.message) {
                setShowAddModal(false);
                setNewTopic({
                    title: '',
                    description: '',
                    difficulty: 'beginner',
                    tags: []
                });
                toast.success(response.data.message || 'Topic created successfully!');
                fetchTopics();
            } else {
                console.error('Invalid response format:', response);
                toast.error('Invalid response format from server');
            }
        } catch (error) {
            console.error('Error creating topic:', error);
            if (error.response) {
                console.error('Error response:', error.response.data);
                toast.error(error.response.data.detail || 'Failed to create topic');
            } else if (error.request) {
                console.error('No response received:', error.request);
                toast.error('No response from server');
            } else {
                console.error('Error setting up request:', error.message);
                toast.error('Error setting up request');
            }
        }
    };

    const handleDeleteTopic = async (id) => {
        if (!id) {
            toast.error('Invalid topic ID');
            return;
        }

        if (window.confirm('Are you sure you want to delete this topic?')) {
            try {
                // Ensure the ID is a string
                const topicId = String(id);
                const response = await topicsApi.delete(topicId);
                if (response.data && response.data.message) {
                    toast.success(response.data.message || 'Topic deleted successfully');
                    fetchTopics();
                } else {
                    toast.error('Failed to delete topic');
                }
            } catch (error) {
                console.error('Error deleting topic:', error);
                if (error.response) {
                    toast.error(error.response.data.message || 'Failed to delete topic');
                } else {
                    toast.error('Failed to delete topic');
                }
            }
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold text-gray-900">Topics</h1>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700"
                >
                    Add Topic
                </button>
            </div>

            {/* Topics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {topics.map((topic) => (
                    <div
                        key={topic._id}
                        className="bg-white shadow rounded-lg p-6 hover:shadow-md transition-shadow"
                    >
                        <div className="flex justify-between items-start">
                            <h3 className="text-lg font-semibold text-gray-900">{topic.title}</h3>
                            <span
                                className={`px-2 py-1 text-xs font-medium rounded-full ${topic.difficulty === 'beginner'
                                    ? 'bg-green-100 text-green-800'
                                    : topic.difficulty === 'intermediate'
                                        ? 'bg-yellow-100 text-yellow-800'
                                        : 'bg-red-100 text-red-800'
                                    }`}
                            >
                                {topic.difficulty}
                            </span>
                        </div>
                        <p className="mt-2 text-gray-500">{topic.description}</p>
                        <div className="mt-4">
                            <div className="w-full bg-gray-200 rounded-full h-2.5">
                                <div
                                    className="bg-primary-600 h-2.5 rounded-full"
                                    style={{ width: `${topic.progress}%` }}
                                ></div>
                            </div>
                            <div className="flex justify-between text-sm text-gray-500 mt-1">
                                <span>Progress</span>
                                <span>{topic.progress}%</span>
                            </div>
                        </div>
                        <div className="mt-4 flex justify-end space-x-2">
                            <button
                                onClick={() => handleDeleteTopic(topic._id)}
                                className="text-red-600 hover:text-red-700"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Add Topic Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center">
                    <div className="bg-white rounded-lg p-6 max-w-md w-full">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Add New Topic</h2>
                        <form onSubmit={handleAddTopic} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Title</label>
                                <input
                                    type="text"
                                    value={newTopic.title}
                                    onChange={(e) => setNewTopic({ ...newTopic, title: e.target.value })}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">
                                    Description
                                </label>
                                <textarea
                                    value={newTopic.description}
                                    onChange={(e) =>
                                        setNewTopic({ ...newTopic, description: e.target.value })
                                    }
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                    rows="3"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">
                                    Difficulty
                                </label>
                                <select
                                    value={newTopic.difficulty}
                                    onChange={(e) =>
                                        setNewTopic({ ...newTopic, difficulty: e.target.value })
                                    }
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                >
                                    <option value="beginner">Beginner</option>
                                    <option value="intermediate">Intermediate</option>
                                    <option value="advanced">Advanced</option>
                                </select>
                            </div>
                            <div className="flex justify-end space-x-3">
                                <button
                                    type="button"
                                    onClick={() => setShowAddModal(false)}
                                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700"
                                >
                                    Add Topic
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
} 