FROM centos:centos7.4.1708
LABEL Project=ecoHub Name=Tetration-Infoblox Version=0.0.1
WORKDIR /app
ADD . /app

# these yum packages are required for infoblox_client
RUN yum -y install python-devel gcc

# install pip and then install dependencies
RUN curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
RUN python get-pip.py
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# set up environment variables
ENV INFOBLOX_WAPI_VERSION="2.5"

# run the app when the container launches
# ENTRYPOINT [ "/bin/bash", "eco_action.sh" ]
ENTRYPOINT [ "python", "eco_action.py" ]