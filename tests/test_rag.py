from fastapi.testclient import TestClient
from rag_agent import router as rag_router
from fastapi import FastAPI

app = FastAPI()
app.include_router(rag_router)

client = TestClient(app)
resp = client.post('/rag/query', json={"query": "dor abdominal em criança", "top_k": 3})
print('status', resp.status_code)
print(resp.json())
