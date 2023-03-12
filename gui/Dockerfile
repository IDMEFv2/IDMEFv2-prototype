FROM registry.fedoraproject.org/fedora-minimal:37

RUN microdnf -y update && microdnf -y install postgresql diffutils patch vim preludedb-pgsql prewikka python-kafka git gettext python3-devel python3-configargparse python3-babel python3-lesscpy python3-setuptools && microdnf clean all

COPY patchs /patchs

WORKDIR /prewikka

RUN git clone https://github.com/SECEF/prototype.git

WORKDIR /prewikka/prototype

RUN mv prewikka prewikka-5.2.0

RUN curl -o prewikka-python3.10.patch https://src.fedoraproject.org/rpms/prewikka/raw/rawhide/f/prewikka-5.2.0-fix_python_3.10.patch

RUN patch -p0 -iprewikka-python3.10.patch

RUN patch -p0 -i/patchs/prewikka-cli.patch

RUN rm prewikka-python3.10.patch

WORKDIR /prewikka/prototype/prewikka-5.2.0

RUN python setup.py install

WORKDIR /

RUN patch -p0 -i/patchs/prewikka-conf.patch

WORKDIR /etc/prewikka/conf.d

RUN patch -p0 -i/patchs/auth.conf.diff

ENTRYPOINT ["/entrypoint.sh"]
