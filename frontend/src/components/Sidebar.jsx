import { Link } from 'react-router-dom';
import {
    HomeIcon,
    BookOpenIcon,
    CalendarIcon,
    ChartBarIcon,
    XMarkIcon
} from '@heroicons/react/24/outline';

export default function Sidebar({ sidebarOpen, setSidebarOpen }) {
    const navigation = [
        { name: 'Dashboard', href: '/', icon: HomeIcon },
        { name: 'Topics', href: '/topics', icon: BookOpenIcon },
        { name: 'Study Plans', href: '/study-plans', icon: CalendarIcon },
        { name: 'Quizzes', href: '/quizzes', icon: ChartBarIcon },
        { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
    ];

    return (
        <div
            className={`fixed top-0 left-0 h-screen w-64 bg-white shadow-lg transform transition-all duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                }`}
        >
            <div className="flex flex-col h-full">
                <div className="flex items-center justify-between p-4 border-b border-gray-200">
                    <button
                        onClick={() => setSidebarOpen(false)}
                        className="p-2 rounded-lg hover:bg-gray-100 transition-colors duration-200"
                    >
                        <XMarkIcon className="h-6 w-6 text-gray-500" />
                    </button>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    {navigation.map((item) => (
                        <Link
                            key={item.name}
                            to={item.href}
                            className="flex items-center px-4 py-3 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200 group"
                        >
                            <item.icon className="h-6 w-6 mr-3 text-gray-500 group-hover:text-primary-600" />
                            <span className="font-medium group-hover:text-primary-600">{item.name}</span>
                        </Link>
                    ))}
                </nav>

                <div className="p-4 border-t border-gray-200">
                    <div className="flex items-center space-x-3">
                        <div>
                            <p className="text-sm font-medium text-gray-900">Made with ❤️ by Ayush</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
} 