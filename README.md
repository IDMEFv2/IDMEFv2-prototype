# IDMEFv2-prototype

The IDMEFv2 prototype is an alert manager compatible with the IDMEFv2 format.

The aim of this prototype is to demonstrate the capacity to build a (cyber and physical) cyphy-siem on top of IDMEFv2 (Incident Detection Message Exchange Format v2)

The prototype is partially based on Prelude OSS (IDMEFv1) and still under heavy development.

The prototype will offer:
* A communication bus based on kakfa
* JSON Alert storage in Elasticsearch
* Web user operating interface (based on Prewikka OSS)
* Python rules based correlator engine (based on Prelude OSS Correlator)
* Log management analysis with Logstash

IDMEFv2-prototype is an effort provided by the SECEF (SECurity Exchange Format) consortium toward IDMEFv2 standardisation.

A pre-release is expected for T2 2023.

More information about IDMEFv2 at : [https://www.idmefv2.org](https://www.idmefv2.org)

# Prototype of IDMEFv2 implementation

This repository provide docker files and docker-compose files for theses services:

  - Kafka
  - Zookeeper
  - Kafdrop
  - Elasticsearch
  - Logstash
  - SIEM Web Interface
  - PostgreSQL

# Run the prototype

Run the following command:
```
make up
```

# Stop the prototype

Run the following command:
```
make down
```

# Clean the prototype

Run the following command:
```
make clean
```

# Exposed services

Following services are exposed:

  - Web interface: http://localhost
  - Alert's database: http://elastic:elastic@localhost:9200
  - Syslog input: tcp://localhost:6514
  - Kafka status: http://localhost:9201
  - Kafka broker http://localhost:9092

# Test your prototype

For exeample, you can send a log that content a failed login from SSH
```
Mar  11 11:00:35 itguxweb2 sshd[24541]: Failed password for root from 12.34.56.78 port 1806
```
with the netcat tool:
```
echo 'Mar  11 11:00:35 itguxweb2 sshd[24541]: Failed password for root from 12.34.56.78 port 1806' | nc localhost 6514
```
