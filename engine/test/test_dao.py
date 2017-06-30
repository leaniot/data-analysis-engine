from engine import interfaces

# Test static method 'get_access_token'
print (interfaces.Dao.get_access_token("yzg963@gmail.com", "yzg134530"))
dao = interfaces.Dao("http://www.mageia.me/api/1.0.0/event_rules/", "yzg963@gmail.com", "yzg134530")
# Test data writing operation
dao["Rpgs86ACCxA7497XvgeCzD"] = {
	"rule_type": "value",
	"rule_op": "gt",
	"rule_obj": 20
}
# Test data reading operation
print (dao["Rpgs86ACCxA7497XvgeCzD"])