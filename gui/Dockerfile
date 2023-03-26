FROM registry.fedoraproject.org/fedora-minimal:37

RUN microdnf -y update && microdnf -y install postgresql diffutils patch vim preludedb-pgsql prewikka python-kafka git gettext python3-devel python3-configargparse python3-babel python3-lesscpy python3-setuptools && microdnf clean all

COPY patchs /patchs

WORKDIR /prewikka

RUN git clone https://github.com/SECEF/prototype.git

WORKDIR /prewikka/prototype

RUN mv prewikka prewikka-5.2.0

RUN patch -p0 -i/patchs/prewikka-5.2.0-fix_python_3.10.patch
RUN patch -p0 -i/patchs/prewikka-cli.patch
RUN patch -p0 -i/patchs/prewikka-idmefv2-dataprovider.patch
RUN patch -p0 -i/patchs/prewikka-load-idmefv2.patch
RUN patch -p0 -i/patchs/prewikka-elastic-interval.patch
RUN patch -p0 -i/patchs/prewikka-idmefdetails.patch
RUN patch -p0 -i/patchs/prewikka-about.patch
RUN patch -p0 -i/patchs/prewikka-idmefv2_filter_name.patch

WORKDIR /prewikka/prototype/prewikka-5.2.0

RUN python setup.py install

ENTRYPOINT ["/entrypoint.sh"]
