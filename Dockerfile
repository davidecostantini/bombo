FROM centos:7
MAINTAINER "davide.costantini@infomentum.co.uk"
RUN rpm -iUvh http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-5.noarch.rpm
RUN yum update -y; yum clean all;
RUN yum install python python-pip -y
COPY ./* /opt/bombo
WORKDIR /opt/bombo
RUN pip install -qr requirements.txt
RUN ln -s /opt/bombo/bombo /bin/bombo
