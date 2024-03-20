import asyncio
import threading
import time
from queue import Queue, Empty
from loguru import logger
from aioconsole import ainput

class Krem(threading.Thread):
	def __init__(self, q):
		threading.Thread.__init__(self, daemon=True, name='krem')
		self.counter = 0
		self.kill = False
		self.q = q

	def do_kill(self):
		self.kill = True
		logger.debug(f'kremthread got do_kill {self} {self.is_alive()}')

	async def subtask(self):
		logger.debug('Running in subtask')
		count = 0
		while True:
			self.q.put_nowait({'source':'subtask', 'count': count})
			await asyncio.sleep(1)
			count += 1

	def run(self) -> None:
		while not self.kill:
			#logger.debug(f'Krem {self.counter}')
			self.q.put_nowait({'source':'krem', 'count':self.counter})
			time.sleep(0.1)
			self.counter += 1
			if self.kill:
				break
		#return f'kremcount{self.counter}'

async def foo(q):
	logger.debug('Running in foo')
	count = 0
	while True:
		#logger.debug(f'foo {count}')
		q.put_nowait({'source':'foo', 'count':count})
		await asyncio.sleep(1)
		count += 1
	#return f'foocount{count}'

async def bar(q):
	logger.debug('Running in bar')
	count = 0
	while True:
		q.put_nowait({'source':'bar', 'count':count})
		#logger.debug(f'bar {count}')
		await asyncio.sleep(2)
		count += 1
	#return f'barcount{count}'

async def qmon(q):
	logger.debug('qmon')
	count = 0
	stats = {}
	while True:
		c = None
		try:
			c = q.get_nowait()
			q.task_done()
		except Empty:
			pass
		if c:
			if c.get('source') not in stats:
				stats[c.get('source')] = 0
			stats[c.get('source')] += c['count']
			logger.info(f'qmon {stats}')
		await asyncio.sleep(0)

async def async_cli(q):
	logger.debug('cli starting')
	count = 0
	while True:
		c = None
		try:
			cmd = await ainput(">>> ")
			if cmd[:1] == 'q':
				break
			await asyncio.sleep(0)
		except Exception as e:
			logger.error(f'Error: {type(e)} {e}')

async def main():
	q = Queue()
	t = Krem(q)
	logger.debug(f'krem {t} {t.counter}')
	kremtask = asyncio.create_task(asyncio.to_thread(t.run))
	try:
		async with asyncio.TaskGroup() as tg:
			footask = tg.create_task(foo(q))
			bartask = tg.create_task(bar(q))
			qmontask = tg.create_task(qmon(q))
			kremsubtask = tg.create_task(t.subtask())
			cli_task = tg.create_task(async_cli(q))
		#results = [footask.result(), bartask.result()]
		#logger.info(f'asyncresults: {results}')
	except KeyboardInterrupt as e:
		# loop = asyncio.get_running_loop()
		logger.warning(f'Caught {type(e)} {e}')
		for t in threading.enumerate():
			logger.info(f'Thread: {t} {t.name} {t.is_alive()}')
	except asyncio.CancelledError as e:
		# kremtask.do_kill()
		# results = [footask.result(), bartask.result()]
		logger.warning(f'Error: {type(e)} {e}')
		logger.info(f'killing kremthread {t}')
		t.do_kill()
		for t in threading.enumerate():
			logger.debug(f'Thread: {t} {t.name} {t.is_alive()}')
	except Exception as e:
		# kremtask.do_kill()
		logger.error(f'Error: {type(e)} {e}')
if __name__ == '__main__':
	try:
		asyncio.run(main())
	except asyncio.CancelledError as e:
		logger.warning(f'Error: {type(e)} {e}')
	except KeyboardInterrupt as e:
		# loop = asyncio.get_running_loop()
		logger.warning(f'Caught {type(e)} {e}')
		for t in threading.enumerate():
			logger.debug(f'Thread: {t} {t.name} {t.is_alive()}')
