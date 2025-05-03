import { useState, useEffect } from 'react';
import { quizzesApi, topicsApi } from '../services/api';
import { toast } from 'react-toastify';

export default function Quizzes() {
    const [quizzes, setQuizzes] = useState([]);
    const [topics, setTopics] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showQuizModal, setShowQuizModal] = useState(false);
    const [currentQuiz, setCurrentQuiz] = useState(null);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState({});
    const [quizResult, setQuizResult] = useState(null);
    const [newQuiz, setNewQuiz] = useState({
        title: '',
        topic_id: '',
        num_questions: 5,
        difficulty: 'medium',
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [quizzesResponse, topicsResponse] = await Promise.all([
                quizzesApi.getAll(),
                topicsApi.getAll()
            ]);

            // Extract quizzes from response
            const quizzesList = quizzesResponse.data?.data?.quizzes || [];
            setQuizzes(quizzesList);

            // Extract topics from response
            const topicsList = topicsResponse.data?.data?.topics || [];
            console.log('Fetched topics:', topicsList); // Debug log
            setTopics(topicsList);

            setLoading(false);
        } catch (error) {
            console.error('Error fetching data:', error);
            console.error('Topics response:', error.response?.data); // Debug log
            setLoading(false);
        }
    };

    const handleGenerateQuiz = async (e) => {
        e.preventDefault();
        try {
            const response = await quizzesApi.generate(newQuiz);
            setQuizzes([...quizzes, response.data.data]);
            setShowAddModal(false);
            setNewQuiz({
                title: '',
                topic_id: '',
                num_questions: 5,
                difficulty: 'medium',
            });
        } catch (error) {
            console.error('Error generating quiz:', error);
        }
    };

    const handleStartQuiz = async (quiz) => {
        setCurrentQuiz(quiz);
        setCurrentQuestionIndex(0);
        setAnswers({});
        setQuizResult(null);
        setShowQuizModal(true);
    };

    const handleNextQuestion = () => {
        if (currentQuestionIndex < currentQuiz.questions.length - 1) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
        }
    };

    const handlePreviousQuestion = () => {
        if (currentQuestionIndex > 0) {
            setCurrentQuestionIndex(currentQuestionIndex - 1);
        }
    };

    const handleAnswerSelect = (questionId, answer) => {
        setAnswers(prev => ({
            ...prev,
            [questionId]: answer
        }));
    };

    const handleSubmitQuiz = async () => {
        try {
            // Convert answers object to array of QuizSubmission objects
            const formattedAnswers = Object.entries(answers).map(([questionId, answer]) => ({
                question_id: parseInt(questionId),
                selected_answer: answer
            }));

            const response = await quizzesApi.take(currentQuiz._id, formattedAnswers);
            const { result, perfect_score, topic_updated } = response.data.data;
            setQuizResult(result);

            // If perfect score, remove the quiz from the list
            if (perfect_score) {
                setQuizzes(prevQuizzes => prevQuizzes.filter(q => q._id !== currentQuiz._id));

                // Show success message
                toast.success(
                    topic_updated
                        ? "Congratulations! You've mastered this quiz. Your topic progress has been updated and a new study plan has been generated."
                        : "Congratulations! You've mastered this quiz.",
                    { autoClose: 5000 }
                );

                // Refresh data after a short delay
                setTimeout(() => {
                    fetchData();
                }, 1000);
            }
        } catch (error) {
            console.error('Error submitting quiz:', error);
            toast.error('Error submitting quiz. Please try again.');
        }
    };

    const handleRefreshQuestions = async (quiz) => {
        try {
            const response = await quizzesApi.generate({
                topic_id: quiz.topic_id,
                num_questions: quiz.questions.length,
                title: quiz.title
            });

            setQuizzes(prevQuizzes =>
                prevQuizzes.map(q => q._id === quiz._id ? response.data.data : q)
            );
            toast.success('Quiz questions refreshed successfully');
        } catch (error) {
            console.error('Error refreshing quiz:', error);
            toast.error('Failed to refresh quiz questions');
        }
    };

    const handleDeleteQuiz = async (quizId) => {
        if (!window.confirm('Are you sure you want to delete this quiz?')) {
            return;
        }

        try {
            await quizzesApi.delete(quizId);
            setQuizzes(prevQuizzes => prevQuizzes.filter(quiz => quiz._id !== quizId));
            toast.success('Quiz deleted successfully');
        } catch (error) {
            console.error('Error deleting quiz:', error);
            toast.error('Failed to delete quiz');
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
                <h1 className="text-2xl font-bold text-gray-900">Quizzes</h1>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700"
                >
                    Generate Quiz
                </button>
            </div>

            {/* Quizzes Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {quizzes.map((quiz) => (
                    <div
                        key={quiz._id}
                        className="bg-white shadow rounded-lg p-6 hover:shadow-md transition-shadow"
                    >
                        <div className="flex justify-between items-start mb-4">
                            <h3 className="text-lg font-semibold text-gray-900">{quiz.title}</h3>
                            <div className="flex space-x-2">
                                <button
                                    onClick={() => handleRefreshQuestions(quiz)}
                                    className="p-2 text-gray-500 hover:text-primary-600 transition-colors"
                                    title="Refresh Questions"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                                    </svg>
                                </button>
                                <button
                                    onClick={() => handleDeleteQuiz(quiz._id)}
                                    className="p-2 text-gray-500 hover:text-red-600 transition-colors"
                                    title="Delete Quiz"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                        <div className="mt-2 space-y-2">
                            <div className="flex items-center text-sm text-gray-500">
                                <span className="mr-2">Topic:</span>
                                <span className="font-medium">
                                    {topics.find((t) => t._id === quiz.topic_id)?.title || 'Unknown Topic'}
                                </span>
                            </div>
                            <div className="flex items-center text-sm text-gray-500">
                                <span className="mr-2">Questions:</span>
                                <span className="font-medium">{quiz.questions.length}</span>
                            </div>
                            <div className="flex items-center text-sm text-gray-500">
                                <span className="mr-2">Difficulty:</span>
                                <span className={`font-medium ${quiz.questions[0]?.difficulty === 'easy'
                                    ? 'text-green-600'
                                    : quiz.questions[0]?.difficulty === 'medium'
                                        ? 'text-yellow-600'
                                        : 'text-red-600'
                                    }`}>
                                    {quiz.questions[0]?.difficulty || 'Medium'}
                                </span>
                            </div>
                        </div>
                        <div className="mt-4 flex justify-end">
                            <button
                                onClick={() => handleStartQuiz(quiz)}
                                className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700"
                            >
                                Start Quiz
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Quiz Modal */}
            {showQuizModal && currentQuiz && (
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center">
                    <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-gray-900">{currentQuiz.title}</h2>
                            <button
                                onClick={() => setShowQuizModal(false)}
                                className="text-gray-500 hover:text-gray-700"
                            >
                                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        {!quizResult ? (
                            <div className="space-y-6">
                                {/* Progress indicator */}
                                <div className="w-full bg-gray-200 rounded-full h-2.5">
                                    <div
                                        className="bg-primary-600 h-2.5 rounded-full transition-all duration-300"
                                        style={{ width: `${((currentQuestionIndex + 1) / currentQuiz.questions.length) * 100}%` }}
                                    ></div>
                                </div>

                                {/* Question counter */}
                                <div className="text-sm text-gray-500 mb-4">
                                    Question {currentQuestionIndex + 1} of {currentQuiz.questions.length}
                                </div>

                                {/* Current question */}
                                <div className="space-y-4">
                                    <p className="text-lg font-medium text-gray-900">
                                        {currentQuiz.questions[currentQuestionIndex].question}
                                    </p>
                                    <div className="space-y-2">
                                        {currentQuiz.questions[currentQuestionIndex].options.map((option, optionIndex) => (
                                            <label
                                                key={optionIndex}
                                                className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${answers[currentQuestionIndex] === String.fromCharCode(65 + optionIndex)
                                                    ? 'bg-primary-50 border-primary-500'
                                                    : 'hover:bg-gray-50'
                                                    }`}
                                            >
                                                <input
                                                    type="radio"
                                                    name={`question-${currentQuestionIndex}`}
                                                    value={String.fromCharCode(65 + optionIndex)}
                                                    checked={answers[currentQuestionIndex] === String.fromCharCode(65 + optionIndex)}
                                                    onChange={(e) => handleAnswerSelect(currentQuestionIndex, e.target.value)}
                                                    className="h-4 w-4 text-primary-600 focus:ring-primary-500"
                                                />
                                                <span className="ml-3">{option}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                {/* Navigation buttons */}
                                <div className="flex justify-between mt-6">
                                    <button
                                        onClick={handlePreviousQuestion}
                                        disabled={currentQuestionIndex === 0}
                                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Previous
                                    </button>
                                    {currentQuestionIndex < currentQuiz.questions.length - 1 ? (
                                        <button
                                            onClick={handleNextQuestion}
                                            disabled={!answers[currentQuestionIndex]}
                                            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            Next
                                        </button>
                                    ) : (
                                        <button
                                            onClick={handleSubmitQuiz}
                                            disabled={Object.keys(answers).length !== currentQuiz.questions.length}
                                            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            Submit Quiz
                                        </button>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                <div className="text-center">
                                    <h3 className="text-2xl font-bold text-gray-900">Quiz Results</h3>
                                    <p className="text-lg text-gray-600 mt-2">Score: {quizResult.score}%</p>
                                    <p className="text-md text-gray-500">
                                        {quizResult.correct_answers} out of {quizResult.total_questions} correct
                                    </p>
                                    {quizResult.score === 100 && (
                                        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                                            <p className="text-green-700">
                                                Congratulations! You've achieved a perfect score!
                                                This quiz will be removed and your topic progress has been updated.
                                            </p>
                                        </div>
                                    )}
                                </div>

                                <div className="space-y-6">
                                    {quizResult.answers.map((result, index) => (
                                        <div
                                            key={index}
                                            className={`p-4 rounded-lg border ${result.is_correct ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                                                }`}
                                        >
                                            <p className="font-medium text-gray-900 mb-2">
                                                {index + 1}. {result.question}
                                            </p>
                                            <p className="text-sm text-gray-600">
                                                Your answer: {result.your_answer}
                                            </p>
                                            {!result.is_correct && (
                                                <p className="text-sm text-gray-600">
                                                    Correct answer: {result.correct_answer}
                                                </p>
                                            )}
                                            <p className="text-sm text-gray-600 mt-2">
                                                {result.explanation}
                                            </p>
                                        </div>
                                    ))}
                                </div>

                                <div className="flex justify-end">
                                    <button
                                        onClick={() => setShowQuizModal(false)}
                                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                                    >
                                        Close
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Generate Quiz Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center">
                    <div className="bg-white rounded-lg p-6 max-w-md w-full">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-gray-900">Generate Quiz</h2>
                            <button
                                onClick={() => setShowAddModal(false)}
                                className="text-gray-500 hover:text-gray-700"
                            >
                                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        <form onSubmit={handleGenerateQuiz} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Title</label>
                                <input
                                    type="text"
                                    value={newQuiz.title}
                                    onChange={(e) => setNewQuiz({ ...newQuiz, title: e.target.value })}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                    placeholder="Enter quiz title"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Topic</label>
                                <select
                                    value={newQuiz.topic_id}
                                    onChange={(e) => setNewQuiz({ ...newQuiz, topic_id: e.target.value })}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                    required
                                >
                                    <option value="">Select a topic</option>
                                    {Array.isArray(topics) && topics.length > 0 ? (
                                        topics.map((topic) => (
                                            <option key={topic._id} value={topic._id}>
                                                {topic.title}
                                            </option>
                                        ))
                                    ) : (
                                        <option value="" disabled>No topics available</option>
                                    )}
                                </select>
                                {topics.length === 0 && (
                                    <p className="mt-1 text-sm text-red-600">
                                        No topics available. Please create a topic first.
                                    </p>
                                )}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">
                                    Number of Questions
                                </label>
                                <input
                                    type="number"
                                    value={newQuiz.num_questions}
                                    onChange={(e) =>
                                        setNewQuiz({ ...newQuiz, num_questions: parseInt(e.target.value) })
                                    }
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                    min="3"
                                    max="20"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Difficulty</label>
                                <select
                                    value={newQuiz.difficulty}
                                    onChange={e => setNewQuiz({ ...newQuiz, difficulty: e.target.value })}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                    required
                                >
                                    <option value="easy">Easy</option>
                                    <option value="medium">Medium</option>
                                    <option value="hard">Hard</option>
                                </select>
                            </div>
                            <div className="flex justify-end space-x-3 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setShowAddModal(false)}
                                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
                                >
                                    Generate Quiz
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
} 