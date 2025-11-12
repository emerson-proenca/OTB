import asyncio
import aiohttp
import time
from faker import Faker

fake = Faker()

API_URL = "http://127.0.0.1:8000/api/register"
TOTAL_USERS = 100 # Número total de usuários a serem criados
CONCURRENCY = 20 # Número de requisições simultâneas

async def create_user(session: aiohttp.ClientSession, user_id: int):
    """Cria um usuário simulando um Member"""
    data = {
        "username": f"user_{user_id}_{fake.user_name()}",
        "email": f"{user_id}_{fake.email()}",
        "password": "12345678",
        "type": "member"
    }
    try:
        async with session.post(API_URL, json=data) as resp:
            status = resp.status
            if status == 201:
                return True
            else:
                error_text = await resp.text()
                print(f"[{user_id}] Erro ({status}): {error_text}")
                return False
    except Exception as e:
        print(f"[{user_id}] Exceção: {e}")
        return False

async def bound_create_user(sem, session, user_id):
    async with sem:
        return await create_user(session, user_id)

async def main():
    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = []
    start_time = time.perf_counter()

    async with aiohttp.ClientSession() as session:
        for i in range(TOTAL_USERS):
            task = asyncio.create_task(bound_create_user(sem, session, i))
            tasks.append(task)

        results = await asyncio.gather(*tasks)

    end_time = time.perf_counter()
    duration = end_time - start_time
    success_count = sum(results)
    fail_count = TOTAL_USERS - success_count
    rps = TOTAL_USERS / duration

    print("\n========== BENCHMARK RESULT ==========")
    print(f"Total users attempted: {TOTAL_USERS}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total time: {duration:.2f} seconds")
    print(f"Requests per second (RPS): {rps:.2f}")
    print(f"Average time per request: {duration / TOTAL_USERS:.4f} sec")
    print("======================================\n")

if __name__ == "__main__":
    asyncio.run(main())
