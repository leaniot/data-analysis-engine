from engine import interfaces

# Test static method 'get_access_token'
print (interfaces.Dao.get_access_token("yzg963@gmail.com", "yzg134530"))
dao = interfaces.Dao("http://119.254.211.60:8000/api/1.0.0/event_rules/", "yzg963@gmail.com", "yzg134530")
# Test data writing operation
dao["5zVcJyaSU4bewkiJpcypg9"] = {
	"rule_type": "value",
	"rule_op": "gt",
	"rule_obj": 4.0
}
# Test data reading operation
print (dao["5zVcJyaSU4bewkiJpcypg9"])