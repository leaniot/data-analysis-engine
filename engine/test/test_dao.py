from engine import interfaces

print interfaces.Dao.get_access_token("yzg963@gmail.com", "yzg134530")
dao = interfaces.Dao("http://www.mageia.me/api/1.0.0/event_rules/", "yzg963@gmail.com", "yzg134530")
print dao["2r6Jq5jPDLhmNW4BjVzBzN"]
# dao[""] = {
#     "rule_op": "lt",
#     "rule_type": "sensor",
#     "rule_obj": "{}",
#     "observers": "user1,user2,user3"
# }