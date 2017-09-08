#!/usr/bin/env python
# -*- coding: utf-8 -*-

import arrow
import json
from engine import interfaces, settings, logger

"""
This module defines all kinds of checker that we could apply on the sensor data.

Particularly, class Checker is an abstract class that provides basic functions like subscribing
data stream, publishing notifications and data accessing API. There are two instantiable classes 
RuleChecker and FeatureChecker are able to use.
"""


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

    def __init__(
            self, dao_url=settings.DAO_URL,
            sub_url=settings.RABBITMQ_URL,
            pub_url=settings.RABBITMQ_URL,
            email=settings.AUTH_EMAIL,
            password=settings.AUTH_PASSWORD,
            data_chn="leaniot.realtime.data",
            notif_chn="leaniot.notification"):

        interfaces.Subscriber.__init__(self, sub_url, data_chn)
        interfaces.Publisher.__init__(self, pub_url)
        self.dao = interfaces.Dao(dao_url, email, password)
        self.data_chn = data_chn
        self.notif_chn = notif_chn

    def stop(self):
        """
        Stop the connections to the message queue
        """

        logger.info ("Stopping the checker service ...")
        # Stop the connections to the message queue
        # TODO: currently, it is an invalid method to stop the connection. I have to ask Zhiyi how
        # do this job correctly.
        self.hs.__del__()
        self.hp.__del__()

    def start(self):
        """
        Start the connections to the message queue
        """

        logger.info ("Starting the checker service ...")
        # Start the connections to the message queue
        self.hs.run()
        
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

        logger.info(msg)
        msg = json.loads(msg.decode('utf-8'))
        logger.info ("\nReceived data from sensor: %s" % msg["sensor_id"])

        # TODO: Only check one specific user's rules which would be indicated by the passing 
        # email and password

        payload_type = msg["data_type"]           # Payload type
        payload      = msg["payload"]             # Payload field of real-time data stream
        lib_info     = self.dao[msg["sensor_id"]] # Rules/Feature Library Information

        # check if there is a existed rule for the current sensor
        if not bool(lib_info):
            logger.info ("There is no library item for sensor Id: %s" % msg["sensor_id"])
            return 

        # Check the data by its payload and its corresponding library information
        assertion, response_msg = self.check(payload_type, payload, lib_info)
        if assertion:
            # TODO: Save the notification message to database
            if lib_info["is_push"]:
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

        logger.info ("Please override this function. Payload: %s, payload type: %s, library info: %s" % \
            (payload, payload_type, lib_info))
        return False, None

    def online_data_callback(self, channel, msg):
        """
        Online Data Callback

        An empty (abstract) function that needs to be overrided if you want to get the online 
        real-time data to do some further process, like monitoring the real-time data.
        """

        logger.info ("[Online Data] channel: %s, msg: %s" % (channel, msg))



class RuleChecker(Checker):
    """
    Rule Checker

    Rule checker is a child class of class Checker. It mainly overrides 'check' function for
    doing specific checking process, and 'online_data_callback' function for checking other 
    traffic if the rule type is 'sensor' (which means the checker has to compare the sensor
    data with another real-time sensor data). It also provides a function for getting any 3rd
    party data source which would be used if the rule type was trd_party.

    Once the object has been substantiated, the data subscriber, the notification publisher and
    the rules checker would start to work immediately. Ideally, every user (a specific email 
    password) would maintain an individuous checker service, which would be easy to deploy them
    distributely. 
    """

    def __init__(self, dao_url, sub_url, pub_url, email, password, data_chn, notif_chn):

        Checker.__init__(self, dao_url, sub_url, pub_url, \
            email, password, data_chn, notif_chn)
        self.target_val      = None
        self.target_sensorid = None
        self.target_3rd      = None
        # Definitions of all the enumerate variables
        self.rule_op_enum_map   = ["gt", "lt", "ge", "le", "eq"]
        self.rule_type_enum_map = ["value", "sensor", "trd_party"]
        self.payload_enum_map = ["number", "number", "gps", "number", "number", "number", "diag", "log"]

    def check(self, payload_type, payload, lib_info):
        """
        Check Rules: Overriding of the check in class Checker

        check function would parse the content of lib_info to get the rule information, with the 
        help of that, it would determine how to check the value of the payload of the real-time  
        sensor data and whether to publish a notification or not. 
        """

        logger.info ("Received payload: %s,\tpayload type: %s" % (payload, payload_type))
        logger.info ("Rule's type: %s,\toperator: %s,\ttarget value:%s" % (\
                self.rule_type_enum_map[lib_info["rule_type"]], \
                self.rule_op_enum_map[lib_info["rule_op"]], \
                lib_info["rule_obj"]))
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
        rule_type = self.rule_type_enum_map[lib_info["rule_type"]]
        if rule_type == "value":
            self.target_val = float(lib_info["rule_obj"])
        elif rule_type == "sensor":
            self.target_sensorid = str(lib_info["rule_obj"])
        elif rule_type == "trd_party":
            self.target_3rd = lib_info["rule_obj"]
            self.target_val = self.get_3rd_value(self.target_3rd)
        else:
            raise Exception("Invalid rule type: %s." % lib_info["rule_type"])

        # 2. [Rule Operator]: "gt", "lt", "ge", "le", "eq"
        operator = self.rule_op_enum_map[lib_info["rule_op"]]
        if (self.target_val != None) and (\
            (operator == "gt" and payload_value > self.target_val) or \
            (operator == "lt" and payload_value < self.target_val) or \
            (operator == "ge" and payload_value >= self.target_val) or \
            (operator == "le" and payload_value <= self.target_val) or \
            (operator == "eq" and payload_value == self.target_val)):
            response = { 
                "lib_info": lib_info,
                "payload_val": payload_value, 
                "target_val": self.target_val, 
                "timestamp": str(arrow.now())
            }
            return True, response
        else:
            return False, None

    def online_data_callback(self, channel, msg):
        """
        Overriding of the online_data_callback in class Checker

        This function would be invoked in the process of 'sub_callback' which would be triggerred if 
        there was a new sensor data comes in. This function would get another copy of the new comming
        data and extract the value of the target sensor data.
        """

        sensor_id    = msg["sensor_id"]
        payload      = msg["payload"]
        payload_type = msg["data_type"]
        # If the sensor id was the specified one in the rule object,
        # then get the online real-time payload value of this sensor.
        if sensor_id == self.target_sensorid:
            self.target_val = self.get_payload_value(payload, payload_type)

    def get_payload_value(self, payload, payload_type):
        """
        Get Paylaod Value

        The funciton parses the payload to get the value of the sensor data. 
        """
        
        if self.payload_enum_map[payload_type] == "number":
            return float(payload)
        # TODO: add parsing process for "gps", "diag" and "log"
        else: 
            logger.info("Unsupported payload type: %s" % self.payload_enum_map[str(payload_type)])
            return None

    @staticmethod
    def get_3rd_value(trd_party_info):
        """
        Get Third Party Value

        The function gets real-time data from an indicated 3rd party data source.
        """
        # TODO:

        return 0


class FeatureChecker(Checker):
    """
    Feature Checker


    """

    def __init__(self, dao_url, sub_url, pub_url, email, password, data_chn, notif_chn):

        Checker.__init__(self, dao_url, sub_url, pub_url, \
            email, password, data_chn, notif_chn)