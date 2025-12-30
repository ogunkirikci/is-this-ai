from redis import Redis
from rq import Worker, Queue, Connection
from app.config import settings

listen = ["default"]

def main():
    redis_conn = Redis.from_url(settings.REDIS_URL)
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen))
        worker.work(with_scheduler=False)

if __name__ == "__main__":
    main()
