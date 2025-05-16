from ninja import NinjaAPI

api = NinjaAPI()

api.add_router(prefix='/jobs', router='job.api.router')