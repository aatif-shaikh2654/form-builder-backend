from fastapi import Request, status
from fastapi.responses import JSONResponse

def generic_error_handle(request: Request, exc: Exception):
    print(exc)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={
        "success": False,
        "message": str(exc)
    })

def error_handler(status_code: int, message: str):
    return JSONResponse(status_code=status_code, content={ "success": False, "message": message })