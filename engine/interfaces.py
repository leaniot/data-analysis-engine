#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains basic interfaces used throughout the whole engine.

The interfaces are realized as abstract base classes (ie., some optional functionality
is provided in the interface itself, so that the interfaces can be subclassed)
"""

import requests

class Dao():
	"""
	Interface (abstract class) for Data Access Operations. An DAO is an abstract dictionary in 
	Python, where you can get access to data by indicating its sensor id.

	>>> dao = Dao(...)
	>>> dao["sensor_id_1"] = {...} # Assigning value
	>>> print dao["sensor_id_2"]   # Getting value
	"""

	def __init__(self, url, email, password):
		self.url     = url
		self.token   = self.get_access_token(email, password)
		self.headers = { "Authorization": "JWT 123%s" % self.token, "Content-Type": "application/json" }
		
	def __getitem__(self, sensor_id):
		r = requests.get(url=self.url, headers=self.headers, params={ "sensor_id": sensor_id })
		print r.status_code
		print r.json()

		# status_code starts with 20*
		if r.status_code / 10 == 20:
			return r.json()
		else:
			raise Exception("Failed to get value.")

	def __setitem__(self, sensor_id, value):
		json = { "sensor": sensor_id }
		json.update(value) 
		r = requests.post(url=self.url, headers=self.headers, json=json)
		# status_code starts with 20*
		if r.status_code / 10 == 20:
			return r.json()
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





