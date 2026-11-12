from fastapi import APIRouter

router = APIRouter(tags=["Server Health"])


@router.get("/")
async def server_health():
    return {
        "success": True,
        "messsage": "Form builder backend running"
    }