import { useState } from 'react';

export default function SidebarToggle({ isOpen, onToggle }) {
    return (
        <button
            onClick={onToggle}
            className="fixed top-4 left-4 z-50 p-2 rounded-lg bg-white shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            aria-label="Toggle sidebar"
        >
            <div className="w-6 h-6 relative">
                <span
                    className={`absolute h-0.5 w-6 bg-gray-700 transform transition-all duration-300 ${isOpen ? 'rotate-45 translate-y-2' : 'translate-y-0'
                        }`}
                />
                <span
                    className={`absolute h-0.5 w-6 bg-gray-700 transform transition-all duration-300 ${isOpen ? 'opacity-0' : 'opacity-100'
                        }`}
                    style={{ top: '8px' }}
                />
                <span
                    className={`absolute h-0.5 w-6 bg-gray-700 transform transition-all duration-300 ${isOpen ? '-rotate-45 translate-y-2' : 'translate-y-4'
                        }`}
                />
            </div>
        </button>
    );
} 