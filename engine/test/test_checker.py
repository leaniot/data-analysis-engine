import time
from engine import checker, settings

# Test abstract class Checker
# checker = checker.Checker()
# Test destruction of the checker object (stop checker service)
# time.sleep(100)
# checker.stop()

# Test class RuleChecker
checker = checker.RuleChecker(
    dao_url=settings.DAO_URL,
    sub_url=settings.RABBITMQ_URL,
    pub_url=settings.RABBITMQ_URL,
    email=settings.AUTH_EMAIL,
    password=settings.AUTH_PASSWORD,
    data_chn=settings.MQ_DATA_CH,
    notif_chn=settings.MQ_NOTIFY_CH
)


while True:
    pass

