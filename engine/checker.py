from engine import interfaces

class RuleChecker(interfaces.Subscriber, interfaces.Publisher):
	"""
	Rule Checker



	"""

	def __init__(self, 
		rule_url="http://www.mageia.me/api/1.0.0/event_rules/",
		data_url="pubsub://leaniot:leaniot@119.254.211.60:5672/",
		email="yzg963@gmail.com",
		password="yzg134530",
		data_chn="leaniot.realtime.data",
		notif_chn="leaniot.notification"):

		interfaces.Subscriber.__init__(self, data_url, data_chn)
		self.dao = interfaces.Dao(rule_url, email, password)
		self.notif_chn = notif_chn

	def check_payload(self, payload_info, payload_type, operator, obj_value):
		"""
		Check Payload

		This function would parse the payload data by the 'paths_map', and 
		get the values that needs to be compared with object values. 
		"""

		# todo: move paths_map to config file

		# Paths Map
		# 0, temperature; 1, memory; 2, geolocation; 3, volt
		# 4, ampere; 5, velocity; 6, diagnostic (object); 7, log
		paths_map = [ "num", "num", ["lat", "lng"], "num", "num", "num", "obj", "obj" ]

		# Get payload value
		payload = Payload(payload_info)
		payload_value = payload[paths_map[payload_type]]
		# todo: check the geolocation type data in the future.
		#       return false (without check) if payload values are lat and lng
		if payload_value == 2 or payload_type == 6 or payload_type == 7:
			return False

		# Rule operator: "gt", "lt", "ge", "le", "eq"
		if (operator == "gt" and payload_value > obj_value) or \
			(operator == "lt" and payload_value < obj_value) or \
			(operator == "ge" and payload_value >= obj_value) or \
			(operator == "le" and payload_value <= obj_value) or \
			(operator == "eq" and payload_value == obj_value):
			return True
		else:
			return False
		
	def sub_callback(self, channel, msg):
		"""
		Override the callback function of interfaces.Subscriber

		"""

		print ("[Subscriber] channel: %s, msg: %s" % (channel, msg))

		payload_type = msg["data_type"]
		payload      = msg["payload"]
		rule_info    = self.dao[msg["sensor_id"]]

		# check if there is a existed rule for the current sensor
		if not bool(rule_info):
			return 

		# Get object by rule type
		# Rule type: "value", "sensor", "trd_party"
		if rule_info["rule_type"] == "value":
			try:
				obj_value = int(rule_info["rule_obj"])
			except ValueError:
				print ("Error!")
		elif rule_info["rule_type"] == "sensor" or rule_info["rule_type"] == "trd_party":
			obj_value = rule_info["rule_obj"]
			# todo: connect to other trd party sources
		else:
			raise Exception("Invalid rule type.")

		# Check the rule
		if self.check_payload(payload, payload_type, rule_info["rule_op"], obj_value):
			# Push the notification to the queue if the rule check has been passed
			self.push_notification("!!!push notification!!!")
			# print ("!!!push notification!!!")

	def push_notification(self, msg):
		"""
		Override the push notification function of interfaces.Publisher

		"""
		self.publish(self.notif_chn, msg)
		


# class FeatureChecker(interfaces.Subscriber, interfaces.Publisher):
# 	pass



class Payload():
	"""
	Payload class is designed for easily getting access to the values that we attempt to 
	measure. You can reach the value by calling:

	>>> payload = Payload(payload_info) # payload_info is the content of payload field
	>>> values  = payload[paths] # paths can be 'num', 'obj', or a list of paths

	"""

	def __init__(self, payload_info):
		self.payload_info = payload_info

	def __getitem__(self, paths):
		"""
		Paths is an array of paths of resources. Each path can determine an unique value in
		the payload. A path is a series of keys which are delimited by commas.

		"""
		# Return the payload directly if it was a numerical value
		if paths == "num":
			return self.payload_info
		# Return None if it was an unresolved object
		elif paths == "obj":
			return None
		# Return the value by the series keys if the paths is a list
		elif type(paths) == list:
			values = []
			for path in paths:
				payload_val = self.payload_info
				for key in path.strip().split(","):
					payload_val = payload_val[key]
				values.append(payload_val)
			return values



if __name__ == "__main__":

	rc = RuleChecker()
	while True:
		pass