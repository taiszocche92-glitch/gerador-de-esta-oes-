import asyncio
from rag_agent import rag_query, RAGQuery

async def run_test():
    body = RAGQuery(query='dor abdominal em criança', top_k=3)
    res = await rag_query(body)
    print(res)

if __name__ == '__main__':
    asyncio.run(run_test())
