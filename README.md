Data Analysis Engine
===

### Introduction

LeanIOT Data Analysis Engine is an integrated platform for large and fast growing industrial sensor data analysis and notification. It builds on a big data platform and a web service container to provide online data analysis restful API. It delivers event registration, online event analysis, real-time notification and offline data mining and many other features as an essential micro service of LeanIOT technical framework. Below is an illustration for the system structure of data analysis engine. 

![data_analysis_engine_sys](https://github.com/leaniot/data-analysis-engine/blob/master/img/LeanIOT%20Data%20Analysis%20Engine.png)
*<p align="center">An illustration for the system structure of data analysis engine.</p>*

The engine mainly contains two key components:

- Big Data Platform: it provides offline data mining to analyze some underlying features of sensor data that users might be interested in, or could help users make administrative decision for their industrial systems. 
- Anomaly Detection Engine: it contains two submodules which both check the online data and analyze them by using pre-defined rules or advanced machine learning techniques, also it delivers real-time notifications for dashboard. 

### Message Queue Services

For handling real-time and asynchronous data feed, and providing real-time push services, two message queues have been created as shown above. One message queue is serving as a data feed, giving the latest real-time data to the subscribers. The other message queue is serving as a push notification services.

### Data Model

The real-time online data stream that we received from subscribed Message Queue Services has an uniform data structure for easier data information extraction. Usually an item of the online data stream can be defined as follow:

```json
{
    "id": "5956025b9e8663418ba82101",       // Data id
    "created": "2017-06-30T07:48:43.506Z",  // Created at
    "modified": "2017-06-30T07:48:43.506Z", // Updated at
    "project_id": "udBwnHWWSJ4G6uwQPmeUgD", // Project id
    "device_id": "as3geiqZyb79XjYLTnraMX",  // Device id
    "sensor_id": "Rpgs86ACCxA7497XvgeCzD",  // Sensor id
    "timestamp": 1498808923155,             // Timestamp when the data has been updated
    "payload": 28.562,                      // Payload of the data that we need to check
    "data_type": 0,                         // A enumerate value that defines the what kinds of data the payload is
    "desc": "28.6 ℃ (83.4 ℉)"               // A brief text description for the payload value
}
```

Basically, the engine would extract and parse the value of the payload, and check if the value conformed to the constrains of the predefined corresponding rules by its user. 

### Library Model

In order to let front-end have more autonomous rights on re-alignment of business, a flexible but dependable back-end micro service, and a finer-grained design of event model, we defined a rule/feature model for each of the sensor. In addtion, the event database is used to store all the notifications that users have registered for further statistical analysis and advanced visualization, we also defined the event model at last of this chapter.

#### Rules Library

A sensor can have one or more related rules or features, and take the latest rule as the active one by default. Noted that the type of the value of `ruleObj` is determined by both `ruleOp` and `ruleType`. For instance, a `ruleObj` is going to be a `sensorId` if `ruleType` was `sensor` and `ruleOp` was `gt`.  

```json
{
    "id": "Uniq Identification for each rule",
    "sensor": "Id of the sensor that the rule applies to",
    "rule_op": "An enum value ('gt', 'lt', 'ge', 'le', 'eq') for the operator of the rule",
    "rule_type": "An enum value (value', 'sensor', 'trd_party') for the data type of the rule",
    "rule_obj": "The object of the rule, which is determined by ruleOp and ruleType",
    "observers": ["userId1", "userId2", ... ], "The list of users who have the rights to subscribe and check the rule", 
    "is_push": true/false,
    "created_at": "The timestamp of creating this rule"
}
```

#### Feature Library

*TBD*

```json
{
    "id": "Uniq Identification for each feature",
    "sensor": "Id of the sensor that the rule applies to",
    "feature_type": "An enum value (TBD) for the feature type",
    "feature_value": "The value of the feature, which is going to be a vector or a matrix",
    "observers": ["userId1", "userId2", ... ], "The list of users who have the rights to subscribe and check the rule",
    "is_push": true/false, 
    "created_at": "The timestamp of creating this feature"
}
```

#### Event Database

*TBD*

```json
{
    "id": "Uniq Identification for each event",
    "event_type": "An enum value ("rule", "feature", "box") for the type of the event",
    "event": "ruleId/featureId/boxEventId",
    "details": {...},
    "created_at": "The timestamp of creating this event"
}
```

### Notification Model

Once the engine detects the anomaly that we predefined in the libraries, it would alert related users who have subscribed this kind anomaly, and send them notifications immediately via the notification message queue service. Therefore, we also gave an uniform definition of the notification model. Every notification message should have the same structure that each of the services which need to subcribe the notifications can parse the message in an identical way. 

```json
{
    "rule_info": // 
        {
            "observers": [], 
            "updated_at": "2017-06-13 10:16:45", 
            "rule_type": 0, 
            "rule_op": 0, 
            "sensor": "Rpgs86ACCxA7497XvgeCzD", 
            "is_push": True, "rule_obj": "20", 
            "id": "bKV5ckU7AdLWmmrg2EtLiU"
        }, 
    "payload_val": 28.687, 
    "target_val": 20.0, 
    "timestamp": "2017-06-30T15:26:46.647567+08:00"
}
```
