.PHONY: max_map_count
max_map_count:
	sudo sysctl -w vm.max_map_count=262144

ELASTIC_MMC :=
ifneq ($(shell cat /proc/sys/vm/max_map_count),262144)
	ELASTIC_MMC := max_map_count
endif

PROTO_DIRS :=
ifeq ($(wildcard elasticsearch_data),)
	PROTO_DIRS = proto_dirs
endif

.PHONY: check_bin
check_bin:
ifeq (,$(shell which podman))
		$(error "podman seems to not be installed")
endif
ifeq (,$(shell which podman-compose))
		$(error "podman-compose seems to not be installed")
endif
ifneq (4,$(shell podman --version | awk '{print $$3}' | head -c 1))
		$(error "podman version is not 4 or more")
endif

.PHONY: proto_dirs
proto_dirs:
	sudo mkdir -pv elasticsearch_data elasticsearch_logs kafka_logs
	sudo chown -R 1000:0 elasticsearch_data elasticsearch_logs

.PHONY: ps
ps: check_bin
	sudo podman ps -a

.PHONY: up
up: check_bin $(ELASTIC_MMC) $(PROTO_DIRS)
	(sudo podman-compose -p proto -f docker-compose.yml up 2>&1 1>>logs &)

.PHONY: down
down: check_bin
	sudo podman-compose -p proto -f docker-compose.yml down

.PHONY: clean
clean: check_bin down
	sudo rm -rvf logs
	sudo rm -rvf elasticsearch_data elasticsearch_logs kafka_logs
	sudo podman rmi localhost/proto_setup localhost/proto_es01 localhost/proto_logstash localhost/proto_kafka1 localhost/proto_zoo1 localhost/proto_kafdrop localhost/proto_gui localhost/proto_postgres
	sudo podman volume rm -f proto_setup proto_postgres

.PHONY: tests_logs
tests_logs: check_bin
	sudo podman build -t proto_tests -f tests/Dockerfile tests/
	sudo podman run --rm --name=proto_tests_logs -v $(shell pwd)/tests/example_logs:/logs:Z,ro -v $(shell pwd)/tests/entrypoint_tests_logs.sh:/entrypoint.sh:Z,ro --net proto_proto --network-alias tests-logs proto_tests

.PHONY: tests_idmefv2
tests_idmefv2: check_bin
	sudo podman build -t proto_tests -f tests/Dockerfile tests/
	sudo podman run --rm --name=proto_tests_idmefv2 -v $(shell pwd)/tests/example_idmefv2:/idmefv2:Z,ro -v $(shell pwd)/tests/entrypoint_tests_idmefv2.py:/entrypoint.sh:Z,ro --net proto_proto --network-alias tests-idmefv2 proto_tests
