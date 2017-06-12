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
		print (self.dao["2r6Jq5jPDLhmNW4BjVzBzN"])
		
	def sub_callback(self, topic, msg):
		print ("User Callback: topic: %s, msg: %s" % (topic, msg))
		sensor_id = msg["id"]
		if self.dao[sensor_id]

if __name__ == "__main__":
	rc = RuleChecker()
	while True:
		pass