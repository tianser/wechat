#!/usr/bin/python 
#encoding=utf-8

from ringbuf import RingBuffer
import multiprocessing

class CircularBuffer(object):
	def __init__(self, capacity):
		self.lock = multiprocessing.Lock()
		self.used = 0
		self.capacity = capacity
		self.buf = RingBuffer(capacity)
	
	def Space(self):
		with self.lock:
			return self.capacity - self.used

	#Read从第一个buf开始读
	def Read(self, size):
		if size <= 0 or size > capacity:
			return None
		
		content=None 
		with self.lock:
			if size > used:
				content = self.buf.read(used)
			else:
				content = self.buf.read(size)
		return content

	def WriteFromHead(self, content, size):
		if size <= 0:
			return None
		with self.lock:
			while True:
				if size + self.used > self.capacity:
					newBuf = RingBuffer(2*self.capacity)
					data = self.buf.read(self.used)
					newBuf.write(data)
					self.capacity = 2 *self.capacity
					self.buf = newBuf
				else:
					old_data=self.buf.read(self.used)
					self.buf.write(content)
					self.buf.write(old_data)
					self.used = self.used + size
					break
		return True

		
	def Write(self, content, size):
		if size <= 0:
			return None

		with self.lock:
			while True:
				if size + self.used > self.capacity:
					newBuf = RingBuffer(2*self.capacity)
					data = self.buf.read(self.used) 
					newBuf.write(data)

					self.capacity = 2 * self.capacity
					self.buf = newBuf
				else:
					self.buf.write(content) 
					self.used = self.used + size
					break
		return True	
