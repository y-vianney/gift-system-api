from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from core import resolve_assignment


origins = [
    # "127.0.0.1:5500",
    "*"
]

app = FastAPI(
    title='Gift System',
    version='1.0',
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas
class KeyRequest(BaseModel):
    key: str = Field(..., min_length=3, max_length=5)

class WorkerResponse(BaseModel):
    worker_name: str


# Routes
@app.get('/')
def ping():
    return {'status': 'Ooook!'}

@app.post('/worker-name', response_model=WorkerResponse)
def fetch_worker_name(payload: KeyRequest):
    key = payload.key.strip()

    res = resolve_assignment(key)
    if not res:
        raise HTTPException(404, "Invalid key")

    return {"worker_name": res.split(" → ")[-1]}