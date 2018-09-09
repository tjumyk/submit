# Use Ubuntu 18.04 (LTS)
# If you want to try the latest LTS release, change it to "ubuntu:latest"
# If you want to try the latest release (regardless of LTS status), change it to "ubuntu:rolling"
FROM ubuntu:18.04

# Maintainer
# Please read the Docker documentation (https://docs.docker.com/) before asking any questions about this file
MAINTAINER Yukai Miao <yukai.miao@unsw.edu.au>

# Use the pre-built locale in Ubuntu minimal
ENV LANG C.UTF-8

## If you want to use other locales, the following section gives an example
#RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
#    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
#ENV LANG en_US.utf8

# Install system utilities
# To avoid caches of APT sources, all the "apt-get install" operations should start with "update" and end with "rm -rf"
# as shown below.
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates wget && rm -rf /var/lib/apt/lists/*

# Install miniconda3
# Always specify the version explicitly instead of using "Miniconda3-latest-Linux-x86_64.sh".
# You can replace miniconda with anaconda if you really want those many packages
RUN wget --quiet -O /usr/local/miniconda.sh https://repo.continuum.io/miniconda/Miniconda3-4.5.11-Linux-x86_64.sh \
  && bash /usr/local/miniconda.sh -b -p /usr/local/miniconda \
  && rm /usr/local/miniconda.sh
ENV PATH /usr/local/miniconda/bin:$PATH

# Set the working directory
WORKDIR /root/test

# Copy the test materials to the working directory
COPY ./test /root/test

# Install pip requirements
RUN pip install -r requirements.txt

# Test entry point
# We use "timeout" as the entry point to limit the execution time as Docker itself does not suppot this natively.
# The "CMD" instruction in the next section specifies the additional parameters that will be appended to the parameter
# list of this entry point. For "timeout", those additional parameters will be the actual command to run.
# For the syntax of the timeout command, please refer to "man timeout".
ENTRYPOINT ["timeout", "-k", "10s", "1h"]

# Test script command
CMD ["python", "test.py"]

# Copy submission at the last step to reuse the build cache for all the previous steps
COPY ./submission /root/test/submission
