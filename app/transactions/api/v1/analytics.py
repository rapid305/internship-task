import logging

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from taskiq.exceptions import TaskiqResultTimeoutError

from app.transactions.taskiq_broker import broker
from app.transactions.tasks.analyze_task import get_transaction_analysis

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scheme_name="Token",
)


@router.post("/transactions")
async def run_analysis():
    try:
        task = await get_transaction_analysis.kiq()
        return {"task_id": task.task_id, "status": "queued", "message": "Task has been queued for execution"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue analysis task: {str(e)}")


@router.get(
    "/transactions/{task_id}",
)
async def get_transaction_analysis_result(task_id: str):
    try:
        result = await broker.result_backend.get_result(task_id)
    except TaskiqResultTimeoutError:
        return {"task_id": task_id, "status": "processing"}
    except Exception as e:
        logger.error(f"Error retrieving task result {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task result: {str(e)}")

    return {"task_id": task_id, "status": "completed", "data": result}
