#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains basic interfaces used throughout the whole engine.

The interfaces are realized as abstract base classes (ie., some optional functionality
is provided in the interface itself, so that the interfaces can be subclassed)
"""

import requests
from engine.rabbitmq_hub import PubSubHub, Pub, Sub

class Dao():
	"""
	Interface (abstract class) for Data Access Operations. A DAO is an abstract dictionary in 
	Python, where you can get access to data by indicating its sensor id.

	Parameters:
	- url:      Database Restful API url
	- email:    User email (userid)
	- password: User password

	>>> dao = Dao(...)
	>>> dao["sensor_id_1"] = {...} # Assigning value
	>>> print dao["sensor_id_2"]   # Getting value
	"""

	def __init__(self, url, email, password):
		self.email    = email
		self.password = password
		self.url      = url
		self.token    = self.get_access_token(self.email, self.password)
		self.headers  = { "Authorization": "JWT %s" % self.token, "Content-Type": "application/json" }
		
	def __getitem__(self, sensor_id):
		r = requests.get(url=self.url, headers=self.headers, params={ "sensor_id": sensor_id })
		# Run with success
		if r.status_code / 10 == 20: # status_code starts with 20*
			return r.json()
		# Invalid token
		elif r.status_code == 401:
			self.token   = self.get_access_token(self.email, self.password)
			self.headers = { "Authorization": "JWT %s" % self.token, "Content-Type": "application/json" }
			self.__getitem__(sensor_id)
		else:
			raise Exception("Failed to get value.")

	def __setitem__(self, sensor_id, value):
		json = { "sensor": sensor_id }
		json.update(value) 
		r = requests.post(url=self.url, headers=self.headers, json=json)
		# status_code starts with 20*
		if r.status_code / 10 == 20:
			return r.json()
		# Invalid token
		elif r.status_code == 401:
			self.token   = self.get_access_token(self.email, self.password)
			self.headers = { "Authorization": "JWT %s" % self.token, "Content-Type": "application/json" }
			self.__setitem__(sensor_id, value)
		else:
			raise Exception("Failed to set value.")

	@staticmethod
	def get_access_token(email, password):
		"""
		Get Access Token from Token Service

		This static method would get access token by sending a formed request to 
		token service
		"""

		url  = "http://mageia.me/api/1.0.0/token/obtain/"
		json = { "email": email, "password": password }
		headers = { "Content-Type": "application/json" }
		r = requests.post(url=url, headers=headers, json=json)
		# status_code starts with 20*
		if r.status_code / 10 == 20:
			return r.json()["token"]
		else: 
			raise Exception("Failed to get access token.")



class Subscriber():
	"""
	Interface (abstract class) for subscribing a specific rabbitmq. A subscriber provides a 
	static method for user to overwrite their callback, which will be triggerred when rabbitmq
	pushs a new message that the subscriber has subscribed. 

	"""

	def __init__(self, urls, channel):
		h = PubSubHub(url=urls)
		h.subscribe(channel, callback=self.sub_callback)
		h.run()

	@staticmethod
	def sub_callback(topic, msg):
		print ("User Callback: topic: %s, msg: %s" % (topic, msg))



class Publisher():
	"""

	"""