# S4S Prototype and Kubernetes

All container are available thought kubernetes.

YML files are stored in `pods` folder.

# Example with minikube

## Install minikube

Follow the procedure from your Linux distribution

## Start minikube

We need to mount a local folder inside minikube to use it inside sub-containers. For the example, we choose "/tmp/minikube".
```
minikube start --mount --mount-string="/tmp/minikube:/mnt/minikube" --memory max --cpus max --driver podman 
```

## Enable minikube metrics

Run the following command
```
minikube addons enable metrics-server
```

## Start the Kubernetes dashboard

Run the following command
```
minikube dashboard --port 20123
```

## Start all pods

Run the following commands
```
kubectl apply -f pods/zoo.yml
kubectl apply -f pods/kafka.yml
kubectl apply -f pods/kafdrop.yml
kubectl apply -f pods/elasticsearch.yml
kubectl apply -f pods/logstash.yml
kubectl apply -f pods/postgres.yml
kubectl apply -f pods/gui.yml
kubectl apply -f pods/nginx.yml
```

## Access services

To access the GUI:
```
http://192.168.49.2:30080
```

To access the Elasticsearch:
```
http://192.168.49.2:30292
```

To access the kafdrop:
```
http://192.168.49.2:30192
```

To access the Logstash logs listenner:
```
http://192.168.49.2:30514
```
