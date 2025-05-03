import { useState, useEffect } from 'react';
import { analyticsApi } from '../services/api';
import {
    ChartBarIcon,
    ClockIcon,
    TrophyIcon,
    BookOpenIcon,
    ArrowTrendingUpIcon,
    CalendarIcon,
    TagIcon
} from '@heroicons/react/24/outline';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';

export default function Analytics() {
    const [analytics, setAnalytics] = useState({
        progress: null,
        topicStats: [],
        streak: null,
        timeDistribution: null,
        recommendations: null
    });
    const [loading, setLoading] = useState(true);
    const [selectedTimeRange, setSelectedTimeRange] = useState('week');
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        fetchAnalytics();
    }, []);

    const fetchAnalytics = async () => {
        try {
            const [progressResponse, topicStatsResponse, streakResponse,
                timeDistributionResponse, recommendationsResponse] = await Promise.all([
                    analyticsApi.getProgress('user1'),
                    analyticsApi.getTopicStats(),
                    analyticsApi.getStreak('user1'),
                    analyticsApi.getTimeDistribution(),
                    analyticsApi.getRecommendations()
                ]);

            setAnalytics({
                progress: progressResponse.data.data,
                topicStats: topicStatsResponse.data.data,
                streak: streakResponse.data.data,
                timeDistribution: timeDistributionResponse.data.data,
                recommendations: recommendationsResponse.data.data
            });
            setLoading(false);
        } catch (error) {
            console.error('Error fetching analytics:', error);
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
            </div>
        );
    }

    // Prepare data for the bar chart
    const progressChartData = analytics.topicStats.slice(0, 8).map(topic => ({
        name: topic.title,
        Progress: topic.progress,
    }));

    return (
        <div className="space-y-8 p-8 bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
            {/* Header Section */}
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
                <div className="inline-flex rounded-xl shadow-sm bg-white p-1 border border-gray-200">
                    {['day', 'week', 'month', 'year'].map((range) => (
                        <button
                            key={range}
                            onClick={() => setSelectedTimeRange(range)}
                            className={`px-4 py-2 text-sm font-medium transition-all duration-300 ${selectedTimeRange === range
                                ? 'bg-primary-600 text-white shadow-md transform scale-105'
                                : 'text-gray-600 hover:bg-gray-100'
                                } ${range === 'day' ? 'rounded-l-lg' : range === 'year' ? 'rounded-r-lg' : ''}`}
                        >
                            {range.charAt(0).toUpperCase() + range.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-primary-500 hover:shadow-xl">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Total Topics</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">{analytics.progress?.total_topics || 0}</p>
                        </div>
                        <div className="p-3 bg-primary-50 rounded-full">
                            <BookOpenIcon className="h-6 w-6 text-primary-600" />
                        </div>
                    </div>
                    <div className="mt-4">
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div
                                className="h-2 bg-primary-500 rounded-full transition-all duration-500"
                                style={{ width: `${analytics.progress?.completion_percentage || 0}%` }}
                            />
                        </div>
                        <p className="mt-2 text-sm text-gray-500">
                            {analytics.progress?.completion_percentage?.toFixed(1) || 0}% Complete
                        </p>
                    </div>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-green-500 hover:shadow-xl">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Study Streak</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">{analytics.streak?.current_streak || 0} days</p>
                        </div>
                        <div className="p-3 bg-green-50 rounded-full">
                            <TrophyIcon className="h-6 w-6 text-green-600" />
                        </div>
                    </div>
                    <p className="mt-2 text-sm text-gray-500">
                        Longest streak: {analytics.streak?.longest_streak || 0} days
                    </p>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-blue-500 hover:shadow-xl">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Time Spent</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">
                                {Math.floor((analytics.progress?.total_time_spent_minutes || 0) / 60)}h
                            </p>
                        </div>
                        <div className="p-3 bg-blue-50 rounded-full">
                            <ClockIcon className="h-6 w-6 text-blue-600" />
                        </div>
                    </div>
                    <p className="mt-2 text-sm text-gray-500">
                        {analytics.progress?.total_time_spent_minutes || 0} minutes total
                    </p>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-purple-500 hover:shadow-xl">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-500">Average Progress</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">
                                {analytics.progress?.avg_progress?.toFixed(1) || 0}%
                            </p>
                        </div>
                        <div className="p-3 bg-purple-50 rounded-full">
                            <ArrowTrendingUpIcon className="h-6 w-6 text-purple-600" />
                        </div>
                    </div>
                    <p className="mt-2 text-sm text-gray-500">
                        Across all topics
                    </p>
                </div>
            </div>

            {/* Tabs */}
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <nav className="flex space-x-1 p-1 bg-gray-50 border-b border-gray-200">
                    {['overview', 'topics', 'time', 'recommendations'].map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-6 py-3 text-sm font-medium rounded-lg transition-all duration-300 ${activeTab === tab
                                ? 'bg-white text-primary-600 shadow-sm transform scale-105'
                                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                                }`}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    ))}
                </nav>

                {/* Tab Content */}
                <div className="p-8">
                    {activeTab === 'overview' && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {/* Progress Chart */}
                            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                                <h3 className="text-lg font-semibold text-gray-900 mb-6">Progress Overview</h3>
                                <div className="h-72 w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={progressChartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="name" tick={{ fontSize: 12 }} interval={0} angle={-15} textAnchor="end" height={60} />
                                            <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                                            <Tooltip formatter={(value) => `${value}%`} />
                                            <Legend />
                                            <Bar dataKey="Progress" fill="#6366f1" radius={[8, 8, 0, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Recent Activity */}
                            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                                <h3 className="text-lg font-semibold text-gray-900 mb-6">Recent Activity</h3>
                                <div className="space-y-4">
                                    {analytics.topicStats
                                        .sort((a, b) => new Date(b.last_studied) - new Date(a.last_studied))
                                        .slice(0, 5)
                                        .map((topic) => (
                                            <div key={topic.id} className="flex items-center justify-between p-4 rounded-xl hover:bg-gray-50 transition-all duration-300">
                                                <div className="flex items-center space-x-4">
                                                    <div className="p-2 bg-primary-50 rounded-full">
                                                        <CalendarIcon className="h-5 w-5 text-primary-600" />
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-900">{topic.title}</p>
                                                        <p className="text-xs text-gray-500">
                                                            {new Date(topic.last_studied).toLocaleDateString()}
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
                    )}

                    {activeTab === 'topics' && (
                        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                            <div className="px-6 py-4 border-b border-gray-100">
                                <h3 className="text-lg font-semibold text-gray-900">Topic Performance</h3>
                            </div>
                            <div className="divide-y divide-gray-100">
                                {analytics.topicStats.map((topic) => (
                                    <div key={topic.id} className="p-6 hover:bg-gray-50 transition-all duration-300">
                                        <div className="flex items-center justify-between">
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium text-gray-900 truncate">
                                                    {topic.title}
                                                </p>
                                                <div className="mt-2 flex items-center space-x-4">
                                                    <div className="flex items-center text-sm text-gray-500">
                                                        <TagIcon className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" />
                                                        {topic.tags.join(', ')}
                                                    </div>
                                                    <div className="flex items-center text-sm text-gray-500">
                                                        <ClockIcon className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" />
                                                        {topic.time_spent_minutes} min
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="ml-4 flex-shrink-0">
                                                <div className="h-2 w-32 bg-gray-100 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-2 bg-primary-500 rounded-full transition-all duration-500"
                                                        style={{ width: `${topic.progress}%` }}
                                                    />
                                                </div>
                                                <p className="mt-1 text-sm text-gray-500 text-right">
                                                    {topic.progress}%
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {activeTab === 'time' && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {/* Time Distribution by Topic */}
                            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                                <h3 className="text-lg font-semibold text-gray-900 mb-6">Time Distribution by Topic</h3>
                                <div className="space-y-4">
                                    {analytics.timeDistribution?.by_topic.map((topic) => (
                                        <div key={topic.topic_id} className="group">
                                            <div className="flex justify-between text-sm mb-1">
                                                <span className="text-gray-700 group-hover:text-gray-900">{topic.title}</span>
                                                <span className="text-gray-500">{topic.time_spent_minutes} min</span>
                                            </div>
                                            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                                                <div
                                                    className="h-2 bg-blue-500 rounded-full transition-all duration-500 group-hover:bg-blue-600"
                                                    style={{
                                                        width: `${(topic.time_spent_minutes / analytics.timeDistribution.total_time_spent_minutes) * 100}%`
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Time Distribution by Tag */}
                            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                                <h3 className="text-lg font-semibold text-gray-900 mb-6">Time Distribution by Tag</h3>
                                <div className="space-y-4">
                                    {analytics.timeDistribution?.by_tag.map((tag) => (
                                        <div key={tag.tag} className="group">
                                            <div className="flex justify-between text-sm mb-1">
                                                <span className="text-gray-700 group-hover:text-gray-900">{tag.tag}</span>
                                                <span className="text-gray-500">{tag.time_spent_minutes} min</span>
                                            </div>
                                            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                                                <div
                                                    className="h-2 bg-green-500 rounded-full transition-all duration-500 group-hover:bg-green-600"
                                                    style={{
                                                        width: `${(tag.time_spent_minutes / analytics.timeDistribution.total_time_spent_minutes) * 100}%`
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'recommendations' && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {/* Neglected Topics */}
                            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                                <h3 className="text-lg font-semibold text-gray-900 mb-6">Neglected Topics</h3>
                                <div className="space-y-4">
                                    {analytics.recommendations?.neglected_topics.map((topic) => (
                                        <div key={topic.id} className="p-4 bg-yellow-50 rounded-xl border border-yellow-100 hover:bg-yellow-100 transition-all duration-300">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <p className="text-sm font-medium text-gray-900">{topic.title}</p>
                                                    <p className="text-xs text-gray-500 mt-1">
                                                        Last studied: {topic.days_since_studied} days ago
                                                    </p>
                                                </div>
                                                <span className="px-3 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                                                    {topic.progress}%
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Almost Complete */}
                            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                                <h3 className="text-lg font-semibold text-gray-900 mb-6">Almost Complete</h3>
                                <div className="space-y-4">
                                    {analytics.recommendations?.almost_complete.map((topic) => (
                                        <div key={topic.id} className="p-4 bg-green-50 rounded-xl border border-green-100 hover:bg-green-100 transition-all duration-300">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <p className="text-sm font-medium text-gray-900">{topic.title}</p>
                                                    <p className="text-xs text-gray-500 mt-1">
                                                        {topic.remaining}% remaining
                                                    </p>
                                                </div>
                                                <span className="px-3 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                                                    {topic.progress}%
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
} 