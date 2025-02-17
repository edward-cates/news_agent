import asyncio
import os
import json

from .gui import TodoApp

async def main():
    with open('local/.env.json', 'r') as f:
        env_vars = json.load(f)
        for key, value in env_vars.items():
            print(f"Writing {key=}")
            os.environ[key] = value

    app = TodoApp()
    await app.run_async()

if __name__ == '__main__':
    asyncio.run(main())

