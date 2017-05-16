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

	"""

	def __init__(self, url, email, password):
		self.url     = url
		self.token   = self.get_access_token(email, password)
		self.headers = { "Authorization": "JWT %s" % self.token, "Content-Type": "application/json" }
		
	def __getitem__(self, sensor_id):
		r = requests.get(url=self.url, headers=self.headers, params={ "sensor_id": sensor_id })
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


print Dao.get_access_token("yzg963@gmail.com", "yzg134530")
dao = Dao("http://www.mageia.me/api/1.0.0/event_rules/", "yzg963@gmail.com", "yzg134530")
dao[""]
# dao[""] = {
#     "rule_op": "lt",
#     "rule_type": "sensor",
#     "rule_obj": "{}",
#     "observers": "user1,user2,user3"
# }

