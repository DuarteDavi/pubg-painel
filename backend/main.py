from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.config import settings
from app.models import Product
from app.routes import admin, auth
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Survival Macro - Access Control",
    version="1.0.0",
    description="Admin panel for managing licenses and access",
)

# CORS - DEBUG
cors_origins_list = settings.get_cors_origins()
logger.info(f"[CORS] Raw cors_origins value: {settings.cors_origins}")
logger.info(f"[CORS] Parsed allow_origins list: {cors_origins_list}")
logger.info(f"[CORS] List type: {type(cors_origins_list)}")
logger.info(f"[CORS] List length: {len(cors_origins_list)}")
for i, origin in enumerate(cors_origins_list):
    logger.info(f"[CORS] Origin {i}: '{origin}' (type: {type(origin).__name__})")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("[CORS] CORSMiddleware registered")

# Create tables
Base.metadata.create_all(bind=engine)

# Seed product
def seed_product():
    db = SessionLocal()
    try:
        existing = db.query(Product).filter(Product.name == "survival_macro").first()
        if not existing:
            product = Product(
                name="survival_macro",
                description="Spray Control - Survival Macro Access Control"
            )
            db.add(product)
            db.commit()
            logger.info("Product 'survival_macro' created")
    except Exception as e:
        logger.error(f"Error seeding product: {e}")
        db.rollback()
    finally:
        db.close()

seed_product()

# Validate admin configuration
def validate_admin_config():
    if not settings.admin_login or not settings.admin_password_hash:
        logger.error("FATAL: Admin credentials not configured")
        logger.error("Run: python app/scripts/setup_admin.py")
        raise RuntimeError("Admin credentials required. Run setup_admin.py first.")

validate_admin_config()

# Routes
app.include_router(auth.router)
app.include_router(admin.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/docs", tags=["docs"], include_in_schema=settings.debug)
async def swagger_ui():
    """Swagger UI - only available in development"""
    if not settings.debug:
        return {"error": "Not available"}
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
