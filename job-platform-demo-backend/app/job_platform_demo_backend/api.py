from ninja import NinjaAPI
from job.api import router as job_router
from company.api import router as company_router

api = NinjaAPI()

api.add_router(prefix='/jobs', router=job_router)
api.add_router(prefix='/companies', router=company_router)