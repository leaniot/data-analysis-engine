import time
from engine import interfaces
from engine.rabbitmq_hub import PubSubHub, Pub, Sub

# Test Publisher class
p = interfaces.Publisher("pubsub://leaniot:leaniot@119.254.211.60:5670/")

# Test Subscriber class
interfaces.Subscriber("pubsub://leaniot:leaniot@119.254.211.60:5670/", "leaniot.realtime.data")
while True:
	p.publish("leaniot.notification.test", "test")
	time.sleep(1)