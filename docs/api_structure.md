# API Structure

## Architecture Overview

The AI-Wardrobe API follows a modular architecture using FastAPI, with clear separation of concerns:

- **Routers** - Handle HTTP requests and responses
- **Models** - Define data structures and validation
- **Database Modules** - Manage data persistence
- **Service Modules** - Implement business logic

## Core Components

### Main Application (`main.py`)

Initializes the FastAPI application with middleware, exception handlers, and router registration.

```python
app = FastAPI(
    title="Virtual Wardrobe API",
    description="API for managing virtual wardrobe and generating outfit suggestions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(CORSMiddleware, ...)

# Global exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc): ...

# Router registration
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(clothing.router)
app.include_router(profile.router)
app.include_router(outfits.router)
```

### Data Models (`models.py`)

Pydantic models for request/response validation and documentation:

```python
class ClothingItem(BaseModel):
    user_id: str
    item_type: str
    material: str
    color: str
    formality: str
    pattern: str
    fit: str
    suitable_for_weather: str
    suitable_for_occasion: str
    sub_type: str
    image_link: Optional[str] = None
```

### API Routers

| Router | Responsibility |
|--------|----------------|
| `auth.py` | User authentication and session management |
| `clothing.py` | CRUD operations for clothing items |
| `outfits.py` | Management of outfit collections |
| `profile.py` | User profile information |
| `chat.py` | AI-powered outfit recommendations |

### Database Integration

Database operations are abstracted into dedicated modules:

```python
# Database connection
supabase: Client = create_client(url, key)

# Example query
response = supabase.table("clothing_items").select("*").execute()
```

### AI Integration

The LLM integration provides intelligent outfit recommendations based on:
- User preferences
- Weather conditions
- Wardrobe contents
- Occasion requirements 