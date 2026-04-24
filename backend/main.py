from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.middleware import RequestLoggingMiddleware, add_cors
from backend.utils.logger import get_logger, setup_logging
from backend.api.health import router as health_router
from backend.api.v1.orders import router as orders_router
from backend.api.v1.products import router as products_router
from backend.api.v1.inventory import router as inventory_router
from backend.api.v1.metrics import router as metrics_router
from backend.api.v1.forecasts import router as forecasts_router
from backend.api.v1.recommendations import router as recommendations_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("VendorIO API starting up")
    yield
    logger.info("VendorIO API shutting down")


app = FastAPI(
    title="VendorIO API",
    description="Small Business E-Commerce Analytics Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

add_cors(app)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router)
app.include_router(orders_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(metrics_router, prefix="/api/v1")
app.include_router(forecasts_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500},
    )
