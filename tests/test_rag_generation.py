import asyncio
from rag_agent import rag_query, RAGQuery

async def run_test():
    body = RAGQuery(query='qual é a principal causa de dor abdominal em criança?', top_k=3, generation_model='pro', max_output_tokens=256)
    res = await rag_query(body)
    print('SUCCESS')
    print(res)

if __name__ == '__main__':
    asyncio.run(run_test())
