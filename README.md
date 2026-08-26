# Nextwave

A full-stack application with a FastAPI backend and React frontend using MongoDB for data persistence.

## Project Structure

```
nextwave/
├── app/
│   ├── backend/          # FastAPI Python backend
│   │   ├── server.py     # Main FastAPI application
│   │   ├── requirements.txt
│   │   └── .env          # Backend environment variables
│   ├── frontend/         # React frontend
│   │   ├── src/          # React source files
│   │   ├── public/       # Static assets
│   │   ├── package.json
│   │   ├── craco.config.js
│   │   └── .env          # Frontend environment variables
│   └── memory/           # Memory storage
├── .venv/                # Python virtual environment
└── package.json          # Root package configuration
```

## Tech Stack

### Backend
- **FastAPI** (0.110.1) - Modern Python web framework
- **Uvicorn** (0.25.0) - ASGI server
- **Motor** (3.3.1) - Async MongoDB driver
- **PyMongo** (4.6.3) - MongoDB driver
- **Pydantic** (2.6.4+) - Data validation
- **python-dotenv** (1.0.1+) - Environment variable management

### Frontend
- **React** (19.0.0) - UI library
- **React Router DOM** (7.18.2) - Routing
- **@tanstack/react-query** (5.56.2) - Data fetching
- **Tailwind CSS** (3.4.17) - Styling
- **Axios** (1.18.0) - HTTP client
- **Radix UI** - Component library

## Prerequisites

- **Python** 3.13+
- **Node.js** 24.19.0+
- **npm** 11.17.0+
- **MongoDB** (running locally or accessible)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd nextwave
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
python -m venv .venv
```

#### Activate Virtual Environment
- **Windows**: `.venv\Scripts\activate`
- **Linux/Mac**: `source .venv/bin/activate`

#### Install Python Dependencies
```bash
cd app/backend
pip install -r requirements.txt
```

#### Configure Backend Environment
Create or edit `app/backend/.env`:
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
```

### 3. Frontend Setup

#### Install Node Dependencies
```bash
cd app/frontend
npm install
```

#### Configure Frontend Environment
Create or edit `app/frontend/.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8000
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
ESLINT_NO_DEV_ERRORS=true
DISABLE_ESLINT_PLUGIN=true
```

## Running the Application

### Start Backend Server

```bash
cd app/backend
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at:
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Start Frontend Development Server

```bash
cd app/frontend
npm start
```

The frontend will be available at:
- **Application**: http://localhost:3000

## API Endpoints

### Health Check
- `GET /api/` - Returns hello world message

### Status Checks
- `POST /api/status` - Create a new status check
- `GET /api/status` - Get all status checks

## Database

The application uses MongoDB for data persistence. Make sure MongoDB is running before starting the backend.

### Database Schema

**StatusCheck Collection**
```json
{
  "id": "uuid",
  "client_name": "string",
  "timestamp": "ISO datetime"
}
```

## Development

### Backend Development
- The backend uses hot-reload with the `--reload` flag
- Changes to Python files will automatically restart the server
- FastAPI provides automatic API documentation at `/docs`

### Frontend Development
- React DevTools are available in the browser
- Changes to React files will automatically reload the application
- Tailwind CSS classes are processed via CRACO

## Troubleshooting

### Backend Issues

**MongoDB Connection Error**
- Ensure MongoDB is running: `mongod`
- Check connection string in `.env` file
- Verify MongoDB is accessible on the specified port

**Port Already in Use**
- Change the port in the uvicorn command: `--port 8001`
- Or kill the process using port 8000

### Frontend Issues

**Module Not Found Errors**
- Ensure all dependencies are installed: `npm install`
- Check import paths in React components

**ESLint Errors**
- ESLint is disabled in the CRACO configuration
- Environment variables `ESLINT_NO_DEV_ERRORS=true` and `DISABLE_ESLINT_PLUGIN=true` are set

**Port Already in Use**
- React will automatically suggest an alternative port
- Or kill the process using port 3000

## Production Deployment

### Backend
- Use a production ASGI server like Gunicorn with Uvicorn workers
- Set up proper CORS origins for production
- Use environment-specific configuration
- Enable proper security headers

### Frontend
- Build the production bundle: `npm run build`
- Serve the static files using a web server like Nginx
- Configure API proxy for production backend URL

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
