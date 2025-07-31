# import asyncio
# from app.core_agent import run_query

# if __name__ == "__main__":
#     query = input("Enter your research query: ")
#     result = asyncio.run(run_query(query))
#     print("\n=== Final Result ===")
#     print(result)

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
