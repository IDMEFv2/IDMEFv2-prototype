FROM registry.fedoraproject.org/fedora-minimal:37

RUN microdnf -y update && microdnf -y install postgresql diffutils patch vim preludedb-pgsql prewikka python-kafka git gettext python3-devel python3-configargparse python3-babel python3-lesscpy python3-setuptools && microdnf clean all

WORKDIR /prewikka

RUN git clone https://github.com/IDMEFv2/IDMEFv2-prototype-gui.git

WORKDIR /prewikka/IDMEFv2-prototype-gui

RUN python setup.py install

ENTRYPOINT ["/entrypoint.sh"]
