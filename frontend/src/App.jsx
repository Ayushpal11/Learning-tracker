import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import SidebarToggle from './components/SidebarToggle';
import Dashboard from './pages/Dashboard';
import Topics from './pages/Topics';
import StudyPlans from './pages/StudyPlans';
import Quizzes from './pages/Quizzes';
import Analytics from './pages/Analytics';

function App() {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <Router>
            <div className="min-h-screen bg-gray-50">
                <ToastContainer position="top-right" autoClose={3000} />
                <SidebarToggle isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
                <Navbar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

                <div className="flex">
                    <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

                    <main className={`flex-1 p-6 transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-0'
                        }`}>
                        <Routes>
                            <Route path="/" element={<Dashboard />} />
                            <Route path="/topics" element={<Topics />} />
                            <Route path="/study-plans" element={<StudyPlans />} />
                            <Route path="/quizzes" element={<Quizzes />} />
                            <Route path="/analytics" element={<Analytics />} />
                        </Routes>
                    </main>
                </div>
            </div>
        </Router>
    );
}

export default App; 