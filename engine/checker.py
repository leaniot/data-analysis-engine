from engine import interfaces

class RuleChecker(Checker):
	"""
	Rule Checker


	"""

	def __init__(self, dao_url, sub_url, pub_url, email, password, data_chn, notif_chn):

		Checker.__init__(self, dao_url, sub_url, pub_url, \
			email, password, data_chn, notif_chn)
		self.target_val      = None
		self.target_sensorid = None
		self.target_3rd      = None

	def check(self, payload_type, payload, lib_info):
		"""
		Check Rules: Overriding of the check in class Checker


		"""

		# Get payload value
		payload_value = self.get_payload_value(payload, payload_type)

		# Parse lib_info (rule)
		# 1. [Rule type]: "value", "sensor", "trd_party"
		#    <value>     means the rule would compare the payload with a indicated value by an
		#                indicated operator.
		#    <sensor>    means the rule would compare the payload with the payload of real-time
		#                data of another indicated sensor by an indicated operator.
		#    <trd_party> means the rule would compare the payload with a trd party data source
		#                by an indicated operator.
		if lib_info["rule_type"] == "value":
			self.target_val = float(lib_info["rule_obj"])
		elif lib_info["rule_type"] == "sensor":
			self.target_sensorid = str(lib_info["rule_obj"])
		elif lib_info["rule_type"] == "trd_party":
			self.target_3rd = str(lib_info["rule_obj"])
			self.target_val = self.get_3rd_value(self.target_3rd)
		else:
			raise Exception("Invalid rule type.")

		# 2. [Rule Operator]: "gt", "lt", "ge", "le", "eq"
		operator = lib_info["rule_op"]
		if (self.target_val != None) and (\
			(operator == "gt" and payload_value > self.target_val) or \
			(operator == "lt" and payload_value < self.target_val) or \
			(operator == "ge" and payload_value >= self.target_val) or \
			(operator == "le" and payload_value <= self.target_val) or \
			(operator == "eq" and payload_value == self.target_val)):
			return True, None
		else:
			return False, None

	def online_data_callback(self, channel, msg):
		"""
		Overriding of the online_data_callback in class Checker


		"""

		sensor_id    = msg["sensor_id"]
		payload      = msg["payload"]
		payload_type = msg["data_type"]
		# If the sensor id was the specified one in the rule object,
		# then get the online real-time payload value of this sensor.
		if sensor_id == self.target_sensorid:
			self.target_val = self.get_payload_value(payload, payload_type)

	@staticmethod
	def get_payload_value(payload, payload_type):
		"""
		Get Paylaod Value


		"""
		payload_map = {
			"0": "number", "1": "number", "2": "gps", "3": "number", 
			"4": "number", "5": "number", "6": "diag", "7":"log"
		}
		if payload_map[str(payload_type)] == "number":
			return float(payload)
		# todo: add parsing process for "gps", "diag" and "log"
		else: 
			print ("Unsupported payload type: %s" % payload_map[str(payload_type)])
			return None


	@staticmethod
	def get_3rd_value(trd_party_name):
		"""
		Get Third Party Value

		"""
		# todo:
		return 0



class FeatureChecker(Checker):
	"""
	Feature Checker

	"""

	def __init__(self, dao_url, sub_url, pub_url, email, password, data_chn, notif_chn):

		Checker.__init__(self, dao_url, sub_url, pub_url, \
			email, password, data_chn, notif_chn)



class Checker(interfaces.Subscriber, interfaces.Publisher):
	"""
	Checker

	An abstract base class for building any kinds of checkers for online real-time data stream. 
	It inherits some properties from two interfaces, Subscriber and Publisher, which means
	this function can receive the latest real-time data from data channel and publish messages 
	to notification channel. You have to define the 'check' function to do the specific checking
	procedure on the real-time data, and give the body of notifications if you need to build
	your checker by inheriting this abstract class. 

	TODO: in the next version, email (username) and password are essential to be provieded for  
	starting a checker for the corresponding user. Only permitted users (who have purchased or  
	subscribed checking service) could be able to maintain a checker service for supervising 
	their real-time online data.

	Params:
	[dao_url]: url for the database of library that you're going to refer.
	[sub_url]: url for the data message queue
	[pub_url]: url for the notification message queue 
	"""

	def __init__(self, 
		dao_url="http://www.mageia.me/api/1.0.0/event_rules/",
		sub_url="pubsub://leaniot:leaniot@119.254.211.60:5672/",
		pub_url="pubsub://leaniot:leaniot@119.254.211.60:5672/",
		email="yzg963@gmail.com",
		password="yzg134530",
		data_chn="leaniot.realtime.data",
		notif_chn="leaniot.notification"):

		interfaces.Subscriber.__init__(self, sub_url, data_chn)
		interfaces.Publisher.__init__(self, pub_url)
		self.dao = interfaces.Dao(dao_url, email, password)
		self.data_chn  = data_chn
		self.notif_chn = notif_chn
		
	def sub_callback(self, channel, msg):
		"""
		Overriding of the callback function of interfaces.Subscriber

		This method receives real-time data stream from the data channel, meanwhile it also 
		retrieves the corresponding library item by the indicated sensor id. Abstract private  
		method 'check' would be invoked to validate the content (payload) of the current real-time
		data if it conformed to any of its constrains (rules in libray). Finally, this method
		would publish a notification to notification channel if anyone of the constrains has 
		been triggerred.    
		"""

		# todo: Only check one specific user's rules which would be indicated by the passing 
		# email and password

		payload_type = msg["data_type"]           # Payload type
		payload      = msg["payload"]             # Payload field of real-time data stream
		lib_info     = self.dao[msg["sensor_id"]] # Rules/Feature Library Information

		# check if there is a existed rule for the current sensor
		if not bool(lib_info):
			print ("Invalid Library item. Sensor Id: %s" % msg["sensor_id"])
			return 

		# Check the data by its payload and its corresponding library information
		assertion, response_msg = self.check(payload_type, payload, lib_info)
		if assertion:
			# Push the notification to the queue if the rule check has been passed
			self.push_notification(response_msg)

		# Online data callback for doing other data processing based on the real-time data stream
		self.online_data_callback(channel, msg)

	def push_notification(self, msg):
		"""
		Overriding of the push notification function of interfaces.Publisher

		This method would publish the passing message to the specific notification channel.
		"""

		self.publish(self.notif_chn, msg)

	def check(self, payload_type, payload, lib_info):
		"""
		Check

		An empty (abstract) function that needs to be overrided to check if the payload conformed 
		to the constrains in the library information (lib_info). If it did, then assert it to be 
		true and return a response that would be published to the notification channel. 
		"""

		print ("Please override this function. Payload: %s, payload type: %s, library info: %s" % \
			payload, payload_type, lib_info)
		return False, None

	def online_data_callback(self, channel, msg):
		"""
		Online Data Callback

		An empty (abstract) function that needs to be overrided if you want to get the online 
		real-time data to do some further process, like monitoring the real-time data.
		"""

		print ("[Online Data] channel: %s, msg: %s" % (channel, msg))