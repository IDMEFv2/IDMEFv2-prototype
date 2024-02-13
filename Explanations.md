# How this prototype is architectured ?

Fully based on podman and podman-compose

One container for each function:
* kafka: broker for each step of data manipulation, from collect to storage, with detection and correlation.
* zoo: (ZooKeeper) centralized service for maintaining configuration of Kafka
* kafdrop: Web interface for Kafka
* elasticsearch: IDMEFv2 and logs storage
* logstash: Data manipulation, detection and correlation
* gui: SIEM Web Interface based on open-source Prelude-SIEM
* postgres: SIEM Web Interface database to store users customizations.
* setup: Initialization of the PostgreSQL and Elasticsearch database and wait for them to be ready

Each repository contains a Dockerfile. It is the description of what the container is made of.

During execution, if a container need to store files, the storage of the databases for exemple, a new folder is automatically create with <container name>_<type of data>. For exemple : elasticsearch_data

All logs goes to the local file "logs"

the podman environement's name is "proto"

# Description of the workflow

## Step one: Inputs and first step of detection

Inputs are managed by Logstash.

The input pipeline is described in the file logstash/pipeline/00-my_collected.conf.

It listens on port 6514 in TCP and UDP and waits for Syslog (RFC5424) messages. You need to configure your local syslog program to send all logs to the 6514 local port.

Messages are cleaned according to the RFC 5424 protocol. The final syslog message is stored in the IDMEFv2 field [Attachment][RawLog] with all information: raw log, facility, severity, timestamp, etc., and [Sensor][0] to represent the sender.

Detection rules stored in the file logstash/rules.yml are executed. Their aim is to indicate if at least one rule matches. If the rule matches, inside fields are extracted (username, URL, email, port source, source IP, destination IP, etc.). Extracted values are stored in the [Attachment][RawLog][Content] field.

In the end, the JSON is sent to Kafka in the "my_collected" topic.
