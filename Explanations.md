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

## Inputs

Inputs are maintained by logstash
