import logging
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import routers
from api.routers import auth, chat, clothing, profile, outfits, weather

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Virtual Wardrobe API",
    description="API for managing virtual wardrobe and generating outfit suggestions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ——— Global Exception Handler ———

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Uncaught exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

# ——— Include Routers ———

# Auth routes
app.include_router(auth.router)

# Chat/AI routes
app.include_router(chat.router)

# Clothing item routes
app.include_router(clothing.router)

# Profile routes
app.include_router(profile.router)

# Outfit routes
app.include_router(outfits.router)

# Weather routes
app.include_router(weather.router)
