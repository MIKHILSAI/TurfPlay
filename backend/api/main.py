from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes.auth import router as auth_router
from backend.api.routes.bookings import router as bookings_router
from backend.api.routes.chat import router as chat_router
from backend.api.routes.equipment import router as equipment_router
from backend.api.routes.membership import router as membership_router
from backend.api.routes.pricing import router as pricing_router
from backend.api.routes.resources import router as resources_router


app = FastAPI(
    title="Turf Booking Agent API",
    description="Backend API for the Turf Booking Agent",
    version="1.0.0",
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        payload = detail
    else:
        payload = {"error_code": "HTTP_ERROR", "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=payload)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(resources_router)
app.include_router(pricing_router)
app.include_router(bookings_router)
app.include_router(membership_router)
app.include_router(equipment_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {"success": True, "message": "Turf Booking Agent API is running"}


@app.get("/health")
def health():
    return {"success": True, "status": "healthy"}