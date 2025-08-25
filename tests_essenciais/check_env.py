from dotenv import load_dotenv
import os
load_dotenv()
keys = [os.getenv(f'GEMINI_API_KEY_{i}') for i in range(1,9)]
print(['set' if k else 'empty' for k in keys])
print(keys)
