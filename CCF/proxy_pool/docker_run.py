from src.scheduler import ProxyScheduler
import subprocess


# FIXME docker中redis如果不是以服务启动，那么就程序启动
def start_redis():
	try:
		cmd = 'redis-server /usr/src/app/redis.conf &'
		subprocess.check_call(cmd, shell=True)
	except Exception as e:
		raise e


start_redis()
ProxyScheduler().run()