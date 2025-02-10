FROM registry.fedoraproject.org/fedora-minimal:37

RUN microdnf -y update && microdnf -y install postgresql diffutils patch vim preludedb-pgsql prewikka python-kafka git gettext python3-devel python3-configargparse python3-babel python3-lesscpy python3-setuptools python3-pytzdata && microdnf clean all

WORKDIR /prewikka

RUN git clone https://github.com/IDMEFv2/IDMEFv2-prototype-gui.git

WORKDIR /prewikka/IDMEFv2-prototype-gui

RUN python setup.py install

RUN ln -s /usr/lib/python3.11/site-packages/pytzdata/zoneinfo /usr/share/zoneinfo

ENTRYPOINT ["/entrypoint.sh"]
