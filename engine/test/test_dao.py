from engine import interfaces

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