import asyncio
import threading
import time
from queue import Queue, Empty
from loguru import logger
class Krem(threading.Thread):
	def __init__(self, q):
		threading.Thread.__init__(self, daemon=True, name='krem')
		self.counter = 0
		self.kill = False
		self.q = q

	def do_kill(self):
		self.kill = True
		logger.debug(f'kremthread got do_kill {self} {self.is_alive()}')

	def run(self) -> None:
		while not self.kill:
			#logger.debug(f'Krem {self.counter}')
			self.q.put_nowait({'krem':self.counter})
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
		q.put_nowait({'foo':count})
		await asyncio.sleep(1)
		count += 1
	#return f'foocount{count}'

async def bar(q):
	logger.debug('Running in bar')
	count = 0
	while True:
		q.put_nowait({'bar':count})
		#logger.debug(f'bar {count}')
		await asyncio.sleep(2)
		count += 1
	#return f'barcount{count}'

async def qmon(q):
	logger.debug('qmon')
	count = 0
	while True:
		c = None
		try:
			c = q.get_nowait()
			q.task_done()
		except Empty:
			pass
		if c:
			logger.info(f'qmon {c}')
		await asyncio.sleep(0)
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
