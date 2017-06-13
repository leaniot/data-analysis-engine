from engine import interfaces
from engine.rabbitmq_hub import PubSubHub, Pub, Sub

# Test DAO class
print (interfaces.Dao.get_access_token("yzg963@gmail.com", "yzg134530"))
dao = interfaces.Dao("http://www.mageia.me/api/1.0.0/event_rules/", "yzg963@gmail.com", "yzg134530")
# print (dao["Rpgs86ACCxA7497XvgeCzD"])
# dao["Rpgs86ACCxA7497XvgeCzD"] = {
# 	"rule_type": "value",
# 	"rule_op": "gt",
# 	"rule_obj": 20
# }
# print (dao["Rpgs86ACCxA7497XvgeCzD"])

# Test Subscriber class
# interfaces.Subscriber("pubsub://leaniot:leaniot@119.254.211.60:5672/", "leaniot.realtime.data")
# while True:
# 	pass

# dao[""] = {
#     "rule_op": "lt",
#     "rule_type": "sensor",
#     "rule_obj": "{}",
#     "observers": "user1,user2,user3"
# }