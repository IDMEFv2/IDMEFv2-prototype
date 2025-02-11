# IDMEFv2-prototype

The IDMEFv2 prototype is an SIEM (Security Information & Event Manager) compatible with the IDMEFv2 format.

The aim of this prototype is to demonstrate the capacity to build a (cyber and
physical) cyphy-siem on top of IDMEFv2 (Incident Detection Message Exchange
Format v2)

The prototype is partially based on Prelude OSS (IDMEFv1) and still under heavy
development but the actual version (2024) is already running.

The prototype will offer:
* A communication bus based on kakfa
* JSON Alert storage in Elasticsearch
* Web user operating interface (based on Prewikka OSS)
* Python rules based correlator engine (based on Prelude OSS Correlator)
* Log management analysis with Logstash
* A test environment with local Linux logs and local webserver

IDMEFv2-prototype is an effort provided by the Safe4Soc (http://safe4soc.eu)  Consortium toward IDMEFv2 standardisation.

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

## Push IDMEFv2 to your prototype

Your prototype is listening on 4690 for IDMEFv2 alerts.

For example, if you have this file `/tmp/test.json` with the following content:

```
{
     "Description": "Potential bruteforce attack on root user account",
     "Priority": "Medium",
     "CreateTime": "2024-10-18T20:55:29.196408+00:00",
     "StartTime": "2021-05-10T16:55:29+00:00",
     "Category": [
       "Attempt.Login"
     ],
     "Analyzer": {
       "Name": "SIEM",
       "Hostname": "siem.acme.com",
       "Type": "Cyber",
       "Model": "Concerto SIEM 5.2",
       "Category": [
         "SIEM",
         "LOG"
       ],
       "Data": [
         "Log"
       ],
       "Method": [
         "Monitor",
         "Signature"
       ],
       "IP": "192.0.2.1"
     },
     "Sensor": [
       {
         "IP": "192.0.2.5",
         "Name": "syslog",
         "Hostname": "www.acme.com",
         "Model": "rsyslog 8.2110",
         "Location": "Server room A1, rack 10"
       }
     ],
     "Target": [
       {
         "IP": "192.0.2.2",
         "Hostname": "www.acme.com",
         "Location": "Server room A1, rack 10",
         "User": "root"
       }
     ]
 }
```

You can send this alert to the prototype using the following command:

```
curl -X POST -sSv http://127.0.0.1:4690 -H "Content-Type: application/json" --data @/tmp/test.json
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

## Write your own parsing rule

For example, you want to parse the following log:
```
Mar  1 12:13:22 rhel7 sshd[70149]: Failed password for invalid user goro from 192.168.133.128 port 55662 ssh2
```

First of all, you need to create the associated pattern in Grok format. It is nearly like REGEX but with high level
framework to help parsing logs.

Here is an explication of Grok: https://docs.mezmo.com/telemetry-pipelines/using-grok-to-parse

Logstash add a lot of pre-built patterns: https://github.com/logstash-plugins/logstash-patterns-core/tree/main/patterns

Here is a Grok validator to help you build Grok patterns: https://grokconstructor.appspot.com/do/match

In our case, the Grok pattern we want is:
```
Failed %{NOTSPACE:[Attachment][RawLog][Content][SSH][auth_method]} for (invalid|illegal) user (?=%{USERNAME:[Attachment][RawLog][Content][related][user]})%{USERNAME:[Attachment][RawLog][Content][destination][user][name]} from %{IPORHOST:[Attachment][RawLog][Content][source][address]} port %{POSINT:[Attachment][RawLog][Content][source][port]:int} ssh2
```

The expected output is:
  - [Attachment][RawLog][Content][SSH][auth_method] => password
  - [Attachment][RawLog][Content][destination][user][name] => goro
  - [Attachment][RawLog][Content][source][address] => 192.168.133.128
  - [Attachment][RawLog][Content][source][port] => 55662

Then, you need to create the "Match" rule for your parsing rule. Create a new file in `logstash/rulesets/<my_file>.yml`.
<my_file> is an arbitrary name for your ruleset file.
Inside your file, you must follow the following format:
```
ruleset:
  name: <ruleset_name>
  description: <A description of your ruleset. Generally, what does the software that generate logs you want to parse>
  field: "[Attachment][RawLog][Content][message]"
  <predicate_if_needed>
  rules:
    - id: <rule_id, must be unique in your whole SIEM installation>
      pattern: <grok_pattern>
      samples:
        - <Example of log>
```

The predicate part is here to increase performance. It allow you to execute the rule only on specific logs. For example, if you want to execute the rule only if field "[Attachment][RawLog][Content][process][name]" is equal to "sshd", the predicate is as this:
```
predicate:
  operator: equal
  operands:
    - operator: variable
      operands: "[Attachment][RawLog][Content][process][name]"
    - operator: constant
      operands: "sshd"
```

In the end, for our example, the ruleset is as follow:
```
ruleset:
  name: ssh
  description: "SSH, is a cryptographic (encrypted) network protocol to allow remote login and other network services to operate securely over an unsecured network."
  field: "[Attachment][RawLog][Content][message]"
  predicate:
    operator: equal
    operands:
      - operator: variable
        operands: "[Attachment][RawLog][Content][process][name]"
      - operator: constant
        operands: "sshd"
  rules:
    - id: 1912
      pattern: "Failed %{NOTSPACE:[Attachment][RawLog][Content][SSH][auth_method]} for (invalid|illegal) user (?=%{USERNAME:[Attachment][RawLog][Content][related][user]})%{USERNAME:[Attachment][RawLog][Content][destination][user][name]} from %{IPORHOST:[Attachment][RawLog][Content][source][address]} port %{POSINT:[Attachment][RawLog][Content][source][port]:int} ssh2"
      outcome: "failure"
      samples:
        - "Mar  1 12:13:22 rhel7 sshd[70149]: Failed password for invalid user goro from 192.168.133.128 port 55662 ssh2"
        - "Jan 14 11:29:17 ras sshd[18163]: Failed publickey for invalid user fred from fec0:0:201::3 port 62788 ssh2"
```

At this stage, all cut-out fields are available inside the log so you can found them in "ARCHIVE" in the web interface.

To create an alert based on this, you need to create a second file here: `logstash/to_idmef/<my_file>.yml`.

Here, the file format is similar:
```
ruleset:
  name: <ruleset_name>
  rules:
    - id: <rule_id>
      <translate if needed>
      fields:
        <list_of fields to fill based on IDMEFv2 format>
```

Remember that IDMEFv2 RFC is available here: https://datatracker.ietf.org/doc/draft-lehmann-idmefv2

<translate> allow you to fill a field conditionally, based on other available fields. For example, if you want to fill the field "Priority" to "Low" all the time but with "Medium" if the user ([Attachment][RawLog][Content][destination][user][name]) is root, you need to use the following synthax:

```
translate:
  - source: "[Attachment][RawLog][Content][destination][user][name]"
    target: "[Priority]"
    dictionary:
      "root": "Medium"
    fallback: "Low"
```

In the end, for our example, the rule is as follow:
```
ruleset:
  name: ssh
  rules:
    - id: 1912
      translate:
        - source: "[Attachment][RawLog][Content][destination][user][name]"
          target: "[Priority]"
          dictionary:
            "root": "Medium"
          fallback: "Low"
      fields:
        "[@metadata][IDMEFv2][source]": "source"
        "[@metadata][IDMEFv2][target]": "host"
        "[Category][0]": "Attempt.Login"
        "[Analyzer][Data]":
          - "Log"
          - "Auth"
        "[Analyzer][Type]": "Cyber"
        "[Source][0][Protocol]":
          - "tcp"
          - "ssh"
        "[Target][0][Service]": "%{[Attachment][RawLog][Content][process][name]}"
        "[Target][0][User]": "%{[Attachment][RawLog][Content][destination][user][name]}"
        "[Description]": "Someone tried to log in as '%{[Attachment][RawLog][Content][destination][user][name]}' from %{[Attachment][RawLog][Content][source][address]} port %{[Attachment][RawLog][Content][source][port]} using the %{[Attachment][RawLog][Content][SSH][auth_method]} method"
```
