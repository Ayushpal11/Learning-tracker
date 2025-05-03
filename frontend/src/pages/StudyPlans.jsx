import { useState, useEffect } from 'react';
import { plansApi } from '../services/api';
import { toast } from 'react-toastify';
import { ClockIcon, TrashIcon, CalendarIcon } from '@heroicons/react/24/outline';

export default function StudyPlans() {
    const [plans, setPlans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [emailPrompt, setEmailPrompt] = useState({ open: false, planId: null });
    const [userEmail, setUserEmail] = useState("");

    useEffect(() => {
        fetchPlans();
    }, []);

    const fetchPlans = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await plansApi.getAll();
            if (response.data && response.data.data) {
                setPlans(response.data.data.plans || []);
            }
        } catch (error) {
            console.error('Error fetching plans:', error);
            toast.error('Failed to fetch study plans');
        } finally {
            setLoading(false);
        }
    };

    const handleActivityComplete = async (planId, activityIndex, completed) => {
        try {
            const response = await plansApi.markActivityComplete(planId, activityIndex, completed);
            if (response.data.data) {
                setPlans(prevPlans =>
                    prevPlans.map(plan =>
                        plan._id === planId ? response.data.data : plan
                    )
                );
                toast.success(`Activity ${completed ? 'completed' : 'uncompleted'}`);
            }
        } catch (error) {
            toast.error('Failed to update activity status');
        }
    };

    const handleDeletePlan = async (planId) => {
        if (!window.confirm('Are you sure you want to delete this study plan?')) {
            return;
        }

        try {
            await plansApi.deletePlan(planId);
            setPlans(prevPlans => prevPlans.filter(plan => plan._id !== planId));
            toast.success('Study plan deleted successfully');
        } catch (error) {
            toast.error('Failed to delete study plan');
        }
    };

    const handleAddToCalendar = (planId) => {
        setEmailPrompt({ open: true, planId });
    };

    const handleSendInvite = async () => {
        if (!userEmail) {
            toast.error('Please enter your email address.');
            return;
        }
        try {
            await plansApi.addToGoogleCalendar(emailPrompt.planId, userEmail);
            toast.success('Invitation sent to your email!');
        } catch (error) {
            toast.error('Failed to send Google Calendar invitation');
        } finally {
            setEmailPrompt({ open: false, planId: null });
            setUserEmail("");
        }
    };

    const ActivityCard = ({ activity, onComplete }) => (
        <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
            <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900">{activity.title}</h3>
                    <div className="flex items-center mt-1">
                        <span className="text-sm text-gray-600 mr-4">
                            <ClockIcon className="w-4 h-4 inline mr-1" />
                            {activity.duration_minutes} minutes
                        </span>
                        <span className={`text-sm px-2 py-1 rounded ${activity.type === 'reading' ? 'bg-blue-100 text-blue-800' :
                            activity.type === 'practice' ? 'bg-green-100 text-green-800' :
                                'bg-gray-100 text-gray-800'
                            }`}>
                            {activity.type}
                        </span>
                    </div>
                </div>
                <button
                    onClick={() => onComplete(activity)}
                    className={`px-3 py-1 rounded-md text-sm font-medium ${activity.completed
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                        }`}
                >
                    {activity.completed ? 'Completed' : 'Mark Complete'}
                </button>
            </div>

            {activity.content && (
                <div className="mt-4 space-y-4">
                    {/* Main Content */}
                    {activity.content.main_content && (
                        <div className="prose prose-sm max-w-none text-gray-600">
                            {activity.content.main_content}
                        </div>
                    )}

                    {/* Key Points */}
                    {activity.content.key_points && activity.content.key_points.length > 0 && (
                        <div>
                            <h4 className="text-sm font-medium text-gray-900 mb-2">Key Points</h4>
                            <ul className="list-disc pl-5 space-y-1">
                                {activity.content.key_points.map((point, idx) => (
                                    <li key={idx} className="text-gray-600 text-sm">{point}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Code Examples */}
                    {activity.content.code_examples && activity.content.code_examples.length > 0 && (
                        <div>
                            <h4 className="text-sm font-medium text-gray-900 mb-2">Code Examples</h4>
                            {activity.content.code_examples.map((example, idx) => (
                                <div key={idx} className="mb-4">
                                    <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto">
                                        <code className={`language-${example.language}`}>
                                            {example.code}
                                        </code>
                                    </pre>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-900">Study Plans</h1>

            <div className="grid grid-cols-1 gap-6">
                {plans.map((plan) => (
                    <div key={plan._id} className="bg-white shadow rounded-lg p-6">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900">
                                    Study Plan for {new Date(plan.date).toLocaleDateString()}
                                </h3>
                                <p className="text-sm text-gray-500 mt-1">
                                    Total Duration: {plan.total_duration_minutes} minutes
                                </p>
                            </div>
                            <div className="flex space-x-2">
                                <button
                                    onClick={() => handleAddToCalendar(plan._id)}
                                    className="p-2 text-gray-400 hover:text-gray-600"
                                    title="Add to Google Calendar"
                                >
                                    <CalendarIcon className="w-5 h-5" />
                                </button>
                                <button
                                    onClick={() => handleDeletePlan(plan._id)}
                                    className="p-2 text-red-400 hover:text-red-600"
                                    title="Delete Plan"
                                >
                                    <TrashIcon className="w-5 h-5" />
                                </button>
                            </div>
                        </div>

                        {/* Activities */}
                        <div className="space-y-4">
                            {plan.activities.map((activity, index) => (
                                <ActivityCard
                                    key={index}
                                    activity={activity}
                                    onComplete={() => handleActivityComplete(plan._id, index, !activity.completed)}
                                />
                            ))}
                        </div>
                    </div>
                ))}

                {plans.length === 0 && (
                    <div className="text-center py-12">
                        <p className="text-gray-500">No study plans available.</p>
                    </div>
                )}
            </div>

            {emailPrompt.open && (
                <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-30 z-50">
                    <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-sm">
                        <h2 className="text-lg font-semibold mb-4">Enter your email to receive a Google Calendar invite</h2>
                        <input
                            type="email"
                            className="w-full border border-gray-300 rounded px-3 py-2 mb-4"
                            placeholder="your@email.com"
                            value={userEmail}
                            onChange={e => setUserEmail(e.target.value)}
                        />
                        <div className="flex justify-end space-x-2">
                            <button
                                className="px-4 py-2 bg-gray-200 rounded"
                                onClick={() => setEmailPrompt({ open: false, planId: null })}
                            >Cancel</button>
                            <button
                                className="px-4 py-2 bg-blue-600 text-white rounded"
                                onClick={handleSendInvite}
                            >Send Invite</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
} 