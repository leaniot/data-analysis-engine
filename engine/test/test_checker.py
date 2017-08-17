import time
from engine import checker

# Test abstract class Checker
checker = checker.Checker()
# Test destruction of the checker object (stop checker service)
# time.sleep(100)
# checker.stop()

# Test class RuleChecker
# checker = checker.RuleChecker(
# 	dao_url="http://www.mageia.me/api/1.0.0/event_rules/",
# 	sub_url="pubsub://leaniot:leaniot@119.254.211.60:5672/",
# 	pub_url="pubsub://leaniot:leaniot@119.254.211.60:5672/",
# 	email="yzg963@gmail.com",
# 	password="yzg134530",
# 	data_chn="leaniot.realtime.data",
# 	notif_chn="leaniot.notification")

while True:
    pass

