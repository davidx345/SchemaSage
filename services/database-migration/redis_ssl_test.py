import redis

HOST = 'redis-16685.c85.us-east-1-2.ec2.redns.redis-cloud.com'
PORT = 16685
USERNAME = 'default'
PASSWORD = 'yjgLl5SUWYxcRhgzWJOVpMkkhGYDpAzO'

def try_redis_connection(ssl_enabled):
    print(f"\nTrying Redis connection with ssl={ssl_enabled}...")
    try:
        r = redis.Redis(
            host=HOST,
            port=PORT,
            decode_responses=True,
            username=USERNAME,
            password=PASSWORD,
            ssl=ssl_enabled,
            ssl_cert_reqs=None if ssl_enabled else None
        )
        success = r.set('foo', 'bar')
        print('SET success:', success)
        result = r.get('foo')
        print('GET result:', result)
        print(f"SUCCESS: Redis connection with ssl={ssl_enabled} works!\n")
    except Exception as e:
        print(f"FAILED: Redis connection with ssl={ssl_enabled} failed: {e}\n")

if __name__ == "__main__":
    try_redis_connection(ssl_enabled=True)
    try_redis_connection(ssl_enabled=False)
