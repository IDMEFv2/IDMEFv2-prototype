# IDMEFv2-prototype

The IDMEFv2 prototype is an alert manager compatible with the IDMEFv2 format.

The aim of this prototype is to demonstrate the capacity to build a (cyber and
physical) cyphy-siem on top of IDMEFv2 (Incident Detection Message Exchange
Format v2)

The prototype is partially based on Prelude OSS (IDMEFv1) and still under heavy
development.

The prototype will offer:
* A communication bus based on kakfa
* JSON Alert storage in Elasticsearch
* Web user operating interface (based on Prewikka OSS)
* Python rules based correlator engine (based on Prelude OSS Correlator)
* Log management analysis with Logstash
* A test environment with local Linux logs and local webserver

IDMEFv2-prototype is an effort provided by the SECEF (SECurity Exchange Format)
consortium toward IDMEFv2 standardisation.

A pre-release is expected for T2 2023.

More information about IDMEFv2 at :
[https://www.idmefv2.org](https://www.idmefv2.org)

# Prototype of IDMEFv2 implementation

This repository provide docker files and docker-compose files for theses
services:

  - Kafka
  - Zookeeper
  - Kafdrop
  - Elasticsearch
  - Logstash
  - SIEM Web Interface
  - PostgreSQL
  - NGINX test Webserver

# Prerequisite

You need :

  - podman version 4 or higher
  - podman-compose version 1 or higher

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
  - IDMEFv2 input: http://localhost:4690
  - Kafka status: http://localhost:9201
  - Kafka broker: http://localhost:9092
  - NGINX test Webserver: http://localhost:8080

# Test your prototype system

## Configure your system to send logs to your prototype

By default, the prototype is listen on localhost on port 6514 port to get logs
on TCP (no SSL) and UDP.

You can configure your own localhost logs to go to the prototype. For example
with rsyslog:
  - Edit /etc/rsyslog.conf
  - At the end of the file, add the following line:
    - *.* @@127.0.0.1:6514
  - Restart the rsyslog process:
    - systemctl restart rsyslog

## Generate errors from your NGINX test webserver

A web server is available by default and already configured to send logs to
prototype. NGINX test webserver has 4 possibles URL:
  - http://localhost to get 200 access code
  - http://localhost/test_403 to get 403 error
  - http://localhost/test_404 to get 404 error
  - http://localhost/test_500 to get 500 error
  - All other URL to get 404 error

To manage the test webwerver, you can use the following commands:
```
make up-test
```
òr
```
make down-test
```
òr
```
make clean-test
```

## Manually send logs to your prototype

For exeample, you can send a log that content a failed login from SSH
```
Mar  11 11:00:35 itguxweb2 sshd[24541]: Failed password for root from 12.34.56.78 port 1806
```
with the netcat tool:
```
echo 'Mar  11 11:00:35 itguxweb2 sshd[24541]: Failed password for root from 12.34.56.78 port 1806' | nc -N localhost 6514
```
or with embeded test container:
```
make tests_logs
```
Note: logs are in `tests/example_logs` file.

You can also try to send an IDMEFv2 alert with embeded test container:
```
make tests_idmefv2
```
Note: IDMEFv2 alerts are in `tests/example_idmefv2` file.
