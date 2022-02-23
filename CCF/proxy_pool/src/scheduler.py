from multiprocessing import Process
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from src.proxyManager import ProxyManager
from src.api import api_server
from src.settings import CHECK_WEBSITES
from src.mylogger import Logger, root


class ProxyScheduler():
	def __init__(self, logger: Logger=root):
		self.logger = logger

	def check_raw_proxies(self):
		ProxyManager().check_raw_proxies()

	def get_free_proxies(self):
		try:
			ProxyManager().get_free_proxies()
		except:
			self.logger.warning('something error', exc_info=True)

	def check_useful_proxies(self, website: str):
		ProxyManager().check_useful_proxies(website)

	def rpush_check_useful_proxies(self, website: str):
		try:
			ProxyManager().rpush_check_useful_proxies(website)
		except:
			self.logger.warning('something error', exc_info=True)

	def start_api_server(self):
		try:
			api_server()
		except:
			self.logger.warning('something error', exc_info=True)
			api_server()

	def run(self):
		# 检测raw proxies进程
		check_raw_proxies_process = Process(target=self.check_raw_proxies)
		# 检测{website}_useful_proxies进程
		check_useful_proxies_processes = []
		for website in CHECK_WEBSITES.keys():
			check_useful_proxies_processes.append(Process(target=self.check_useful_proxies, args=(website,)))

		# api server进程
		api_server_process = Process(target=self.start_api_server)

		# 前台定时任务, 会阻塞防止程序退出
		block_scheduler = BlockingScheduler()
		block_scheduler.add_job(self.get_free_proxies, 'interval', minutes=3, id='get_free_proxies', name="get_free_proxies")

		# 后台定时任务
		background_scheduler = BackgroundScheduler()
		for website in CHECK_WEBSITES.keys():
			background_scheduler.add_job(self.rpush_check_useful_proxies, 'interval',
			                             args=(website, ),
			                             seconds=CHECK_WEBSITES[website]['test_cycle'],
			                             id='rpush_{website}_check_useful_proxies'.format(website=website),
			                             name='rpush_{website}_check_useful_proxies'.format(website=website))

		'''
			先实例化一个proxy_manager, 使得在全局已经存在单例proxy_manager,
			不然在启动下面三个process时，会在每个process中都实例化一个proxy_manager
		'''
		ProxyManager()
		api_server_process.start()

		for check_useful_proxies_process in check_useful_proxies_processes:
			check_useful_proxies_process.start()

		check_raw_proxies_process.start()

		# 启动后台定时任务
		background_scheduler.start()

		# 先获取一次free proxies
		self.get_free_proxies()
		# 启动前台定时任务
		block_scheduler.start()


if __name__ == '__main__':
	ProxyScheduler().run()