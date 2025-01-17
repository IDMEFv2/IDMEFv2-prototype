Next action to improve the S4SOC prototype

# More alerts type/format/etc.

We need more diversity in the alert stored : cyber, physical, login, anti-virus, camera, etc.

# Enable the ILM workflow in Elasticsearch

For now, all logs and alerts goes to the Elasticsearch database so hard drive disk is more and more used. At the end, the hard drive will be full and service will stop.

# Dispatch Logstash files into multiple files

To make the prototype works relly fast, the prototype is only few files and is it quite complicated to understand everything.

# Logs storage has maybe too many information

Logs are collected from my_collected kafka topic.

# Enable the IDMEFv2 detail in web interface

Pop-up are showing but tables are empty.

# Enalbe github "action" feature

# Improve Dockerfile files

Rebuild the whole image in the Dockerfile instead of just doing 'FROM postgres' for example.
Use alpine images

# Export to an other repositories the GUI and Correlator

# Add documentation to add nginx in front of the prototype

# Automatically create mapping in a clean run

# Update all docker images
