from django.http.request import HttpRequest
from ninja import Router

from job.schemas import JobCreationRequest

router = Router()


@router.post("")
def create_job(request: HttpRequest, payload: JobCreationRequest):
    return {"status": "Job created"}
