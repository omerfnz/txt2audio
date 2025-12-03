from fastapi import Request, status
from fastapi.responses import JSONResponse
from .logging import logger

async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch all unhandled exceptions.
    Logs the error and returns a standard error response.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error",
            "message": str(exc)
        }
    )
