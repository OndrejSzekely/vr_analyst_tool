FROM python:3

RUN pip3 install simplejson
RUN pip3 install tqdm
RUN pip3 install watson-developer-cloud
RUN pip3 install numpy
RUN pip3 install pillow
RUN pip3 install matplotlib

#OPENCV3 INSTALLATION
RUN apt-get update && \
        apt-get install -y \
        build-essential \
	opencv-data \
	libopencv-dev\
        cmake \
        git \
        wget \
        unzip \
        yasm \
        pkg-config \
        libswscale-dev \
        libtbb2 \
        libtbb-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libavformat-dev \
        libpq-dev \
	qt5-default

RUN wget https://github.com/opencv/opencv_contrib/archive/3.4.2.zip \
	&& unzip 3.4.2.zip \
	&& rm 3.4.2.zip

RUN wget https://github.com/opencv/opencv/archive/3.4.2.zip \
	&& unzip 3.4.2.zip \
	&& rm 3.4.2.zip

RUN mkdir opencv-3.4.2/build &&\
	cd /opencv-3.4.2/build &&\
	cmake -DCMAKE_BUILD_TYPE=RELEASE \
      -DCMAKE_INSTALL_PREFIX=/usr/local \
      -DWITH_TBB=ON \
      -DWITH_V4L=ON \
      -DWITH_QT=ON \
      -DWITH_OPENGL=ON \
      -DOPENCV_EXTRA_MODULES_PATH=../../opencv_contrib-3.4.2/modules \
      -DPYTHON_EXECUTABLE=$(which python3) \
      -DPYTHON_INCLUDE_DIR=$(python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
      -DPYTHON_PACKAGES_PATH=$(python3 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") .. &&\
	make install
RUN rm -r /opencv-3.4.2
RUN rm -r /opencv_contrib-3.4.2


#VR ANALYST TOOL INSTALLATION
RUN wget https://github.com/OndrejSzekely/vr_analyst_tool/archive/master.zip && \
	unzip master.zip && \
	rm master.zip
RUN mkdir /opt/vr_analyst_tool && \
	mv /vr_analyst_tool-master/* /opt/vr_analyst_tool/
RUN cd root/ 
ENV PYTHONPATH "${PYTHONPATH}:/opt/vr_analyst_tool "
