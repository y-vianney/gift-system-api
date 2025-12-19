from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from gift_system import view


app = FastAPI(
    title='Gift System',
    version='1.0',
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

    wn = view(key)
    if wn is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid key or no assignment"
        )

    return {
        'data': {
            'worker_name': wn
        }
    }