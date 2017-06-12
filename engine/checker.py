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
		data_chn="leaniot.realtime.data"):

		interfaces.Subscriber.__init__(self, data_url, data_chn)
		self.dao = interfaces.Dao(rule_url, email, password)
		
	def sub_callback(self, topic, msg):
		print ("User Callback: topic: %s, msg: %s" % (topic, msg))

		payload   = msg["payload"]
		rule_info = self.dao[msg["id"]]
		# check if there is a existed rule for the current sensor
		if not bool(rule_info):
			return 

		# Rule type: "value", "sensor", "trd_party"
		if rule_info["rule_type"] == "value":
			try:
				obj_value = int(rule_info["rule_obj"])
			except ValueError, m:
				print ("Error!")
		elif rule_info["rule_type"] == "sensor" or rule_info["rule_type"] == "trd_party":
			obj_value = rule_info["rule_obj"]
			# todo: connect to other trd party sources
		else:
			raise Exception("Invalid rule type.")

		# Rule operator: "gt", "lt", "ge", "le", "eq"
		if (rule_info["rule_op"] == "gt" and payload > obj_value) or \
			(rule_info["rule_op"] == "lt" and payload < obj_value) or \
			(rule_info["rule_op"] == "ge" and payload >= obj_value) or \
			(rule_info["rule_op"] == "le" and payload <= obj_value) or \
			(rule_info["rule_op"] == "eq" and payload == obj_value)
			self.push_notification("")

	def push_notification(self, msg):
		pass
		


if __name__ == "__main__":

	rc = RuleChecker()
	while True:
		pass