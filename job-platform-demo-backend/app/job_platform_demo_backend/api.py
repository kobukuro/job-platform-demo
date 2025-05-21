from ninja import NinjaAPI
from job.api import router as job_router
from company.api import router as company_router
from user.api import router as user_router

api = NinjaAPI()

api.add_router(prefix='/jobs', router=job_router)
api.add_router(prefix='/companies', router=company_router)
api.add_router(prefix='/users', router=user_router)
