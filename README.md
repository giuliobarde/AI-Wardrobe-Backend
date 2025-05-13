# AI-Wardrobe Backend

## Overview
The AI-Wardrobe backend is built with FastAPI and provides a RESTful API for managing virtual wardrobes, user authentication, outfit generation, and AI-powered clothing recommendations. The backend uses Supabase for data storage and authentication services.

## Tech Stack
- **Framework**: FastAPI
- **Database**: Supabase
- **Authentication**: JWT-based auth via Supabase
- **Image Storage**: Supabase Storage
- **LLM Integration**: AI-powered outfit recommendations via Langchain

## Key Features
- User authentication and profile management
- Virtual wardrobe management with detailed clothing attributes
- AI-powered outfit recommendations based on weather, occasion, and user preferences
- RESTful API with comprehensive endpoint coverage
- Secure data handling with proper authentication

## Project Structure
```
backend/
├── fastapi/
│   ├── api/
│   │   ├── Database/       # Database interaction modules
│   │   ├── llm/            # LLM integration for outfit recommendations
│   │   ├── routers/        # API route definitions
│   │   ├── Weather/        # Weather integration services
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── models.py       # Pydantic data models
│   │   └── test.py         # Test scripts
```

## Documentation
For more detailed information about the API endpoints, database schema, and development guidelines, see the [docs](./docs) directory.

## Setup and Installation

### Prerequisites
- Python 3.8+
- Supabase account and project

### Environment Variables
Required environment variables:
```
SUPABASE_URL=your_supabase_url
SUPABASE_ROLE_KEY=your_supabase_service_role_key
OPENAI_API_KEY=your_openai_api_key
```

### Quick Start
1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment
4. Install dependencies: `pip install -r requirements.txt`
5. Start the development server: `uvicorn api.main:app --reload`

## API Documentation
When running the server, interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /sign-up/`: Register a new user
- `POST /sign-in/`: Authenticate a user and get session token
- `GET /session/`: Validate and get current session information
- `POST /sign-out/`: End the current user session

### Clothing Items
- `POST /add_clothing_item/`: Add a new clothing item to user's wardrobe
- `GET /clothing_items/`: Get all clothing items for a user
- `GET /clothing_item/{item_id}`: Get details of a specific clothing item
- `PUT /update_clothing_item/{item_id}`: Update a clothing item
- `DELETE /delete_clothing_item/{item_id}`: Delete a clothing item

### Outfits
- `POST /create_outfit/`: Create a new outfit from clothing items
- `GET /outfits/`: Get all outfits for a user
- `GET /outfit/{outfit_id}`: Get details of a specific outfit
- `PUT /update_outfit/{outfit_id}`: Update an outfit
- `DELETE /delete_outfit/{outfit_id}`: Delete an outfit

### Profile
- `GET /profile/`: Get user profile information
- `PUT /update_profile/`: Update user profile information

### AI Chat
- `POST /chat/`: Get AI-powered outfit recommendations

## Database Schema

### Users
Stores user authentication and profile information.

### Clothing Items
Stores information about individual clothing items including:
- Type (top, bottom, outerwear, etc.)
- Material
- Color
- Formality
- Pattern
- Fit
- Weather suitability
- Occasion suitability
- Image reference

### Outfits
Stores collections of clothing items that form complete outfits.

### User Preferences
Stores user style preferences for AI recommendations.

## Authentication Flow
The backend uses Supabase for authentication:
1. User signs up/signs in through the API
2. Supabase validates credentials and returns JWT
3. JWT is used for subsequent authenticated requests
4. Token validation happens through middleware

## Development Guidelines

### Adding New Endpoints
1. Create appropriate Pydantic models in `models.py`
2. Add database functions in the relevant module under `Database/`
3. Create route handlers in the appropriate router file
4. Register the router in `main.py` if creating a new router

### Error Handling
All endpoints should use proper exception handling with appropriate HTTP status codes.

### Testing
Run tests using the test scripts in `test.py`.