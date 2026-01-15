from fastapi import FastAPI
from routers.users import router as users_router

app = FastAPI(title="Tarea 01 - FastAPI + MongoDB")

app.include_router(users_router)

@app.get("/")
def root():
    return {"message": "API funcionando. Ve a /docs"}
