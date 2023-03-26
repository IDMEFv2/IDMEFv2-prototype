FROM registry.fedoraproject.org/fedora-minimal:37

RUN microdnf -y update && microdnf -y install vim python3-devel python3-setuptools nc python3-kafka && microdnf clean all

ENTRYPOINT ["/entrypoint.sh"]
