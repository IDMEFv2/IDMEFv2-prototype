#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import sys

with open('/idmefv2', 'r') as f:
    my_idmefv2 = json.loads(f.read())

producer = KafkaProducer(bootstrap_servers=['kafka1:9092'])
for idmefv2 in my_idmefv2:
    producer.send('my_processed', json.dumps(idmefv2).encode('utf-8'))
producer.flush()

print ("IDMEFv2 sent")
sys.stdout.flush()
