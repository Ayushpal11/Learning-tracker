# Learning Tracker

A full-stack application designed to help users track and manage their learning progress across various topics. The application provides features for organizing study plans, managing resources, tracking progress, and taking quizzes.

## 🚀 Features

- **Topic Management**: Create and organize learning topics
- **Study Plans**: Create and manage structured study plans
- **Resource Management**: Store and organize learning resources
- **Progress Analytics**: Track and visualize learning progress
- **Quiz System**: Create and take quizzes to test knowledge
- **Modern UI**: Built with React and Tailwind CSS
- **RESTful API**: FastAPI backend with MongoDB integration

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: MongoDB
- **Authentication**: JWT
- **Dependencies**:
  - FastAPI >= 0.110.0
  - Motor >= 3.3.1
  - Pymongo >= 4.6.0
  - Pydantic >= 2.5.2
  - And more (see requirements.txt)

### Frontend
- **Framework**: React
- **Styling**: Tailwind CSS
- **UI Components**: Headless UI, Heroicons
- **State Management**: React Context
- **HTTP Client**: Axios
- **Charts**: Recharts
- **Notifications**: React Hot Toast

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 14+
- MongoDB
- npm or yarn

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd app
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file with necessary configurations (MongoDB connection, JWT secret, etc.)

5. Run the backend server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

## 📚 Project Structure

```
learning-tracker/
├── app/                    # Backend directory
│   ├── models/            # Database models
│   ├── routes/            # API routes
│   ├── db.py              # Database configuration
│   ├── main.py            # FastAPI application
│   └── requirements.txt   # Python dependencies
│
└── frontend/              # Frontend directory
    ├── public/            # Static files
    ├── src/               # React source code
    │   ├── components/    # React components
    │   ├── pages/         # Page components
    │   └── App.js         # Main application
    └── package.json       # Node.js dependencies
```

## 🔒 Environment Variables

### Backend (.env)
```
MONGODB_URL=your_mongodb_connection_string
JWT_SECRET=your_jwt_secret
```

## 📝 API Documentation

Once the backend server is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- Ayush Pal
