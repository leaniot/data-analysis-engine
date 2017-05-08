Data Analysis Engine
===

### Introduction

LeanIOT Data Analysis Engine is an integrated platform for large and fast growing industrial sensor data analysis and notification. It builds on a big data platform and a web service container to provide online data analysis restful API. It delivers event registration, online event analysis, real-time notification and offline data mining and many other features as an essential micro service of LeanIOT technical framework. Below is an illustration for the system structure of data analysis engine. 

![data_analysis_engine_sys](https://github.com/leaniot/data-analysis-engine/blob/master/img/LeanIOT%20Data%20Analysis%20Engine.png)
*<p align="center">An illustration for the system structure of data analysis engine.</p>*

The engine mainly contains two key components:

- Big Data Platform: it provides offline data mining to analyze some underlying features of sensor data that users might be interested in, or could help users make administrative decision for their industrial systems. 
- Anomaly Detection Engine: it contains two submodules which both check the online data and analyze them by using pre-defined rules or advanced machine learning techniques, also it delivers real-time notifications for dashboard. 

### Data Model

In order to let front end have more autonomous rights on re-alignment of business, and a flexible but dependable back end micro service, and a finer-grained design of event, we defined a rule/feature model for each of the sensor. The event database is used to store all the notifications that users have registered for further statistical analysis and advanced visualization.

#### Rules Library

A sensor can have one or more related rules or features, and take the latest rule as the active one by default. Noted that the type of the value of `ruleObj` is determined by both `ruleOp` and `ruleType`. For instance, a `ruleObj` is going to be a `sensorId` if `ruleType` was `sensor` and `ruleOp` was `gt`.  

```json
{
    "id": "Uniq Identification for each rule",
    "sensorId": "Id of the sensor that the rule applies to",
    "ruleOp": "An enum value ('gt', 'lt', 'ge', 'le', 'eq') for the operator of the rule",
    "ruleType": "An enum value ('value', 'sensor', 'trdParty') for the data type of the rule",
    "ruleObj": "The object of the rule, which is determined by ruleOp and ruleType",
    "observers": ["userId1", "userId2", ... ], "The list of users who have the rights to subscribe and check the rule", 
    "createdAt": "The timestamp of creating this rule"
}
```

#### Feature Library



```json
{
    "id": "Uniq Identification for each feature",
    "sensorId": "Id of the sensor that the rule applies to",
    "featureType": "An enum value (TBD) for the feature type",
    "featureValue": "The value of the feature, which is going to be a vector or a matrix",
    "observers": ["userId1", "userId2", ... ], "The list of users who have the rights to subscribe and check the rule", 
    "createdAt": "The timestamp of creating this feature"
}
```

#### Event Database



```json
{
	"id": "Uniq Identification for each event",
    "eventType": "An enum value ('rule', 'feature', 'box') for the type of the event",
    "eventId": "ruleId/featureId/boxEventId",
    "details": {...},
    "createdAt": "The timestamp of creating this event"
}
```

