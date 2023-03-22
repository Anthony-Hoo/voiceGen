# Use nvidia/cuda image
FROM nvidia/cuda:11.6.0-cudnn8-runtime-ubuntu20.04

COPY ./db/character.db /var/www/character.db
COPY ./db/genshinVoice.db /var/www/genshinVoice.db
COPY ./requirements.txt /var/www/requirements.txt
COPY ./app.py /var/www/app.py
COPY config.yaml /var/www/config.py
COPY ./run.py /var/www/run.py

# set bash as current shell
RUN chsh -s /bin/bash
SHELL ["/bin/bash", "-c"]

# install anaconda
RUN  sed -i s@/archive.ubuntu.com/@/mirrors.pku.edu.cn/@g /etc/apt/sources.list
RUN  apt-get clean

RUN apt-get update
RUN apt-get install -y wget bzip2 ca-certificates libglib2.0-0 libxext6 libsm6 libxrender1 git mercurial subversion && \
        apt-get clean
RUN wget --quiet https://mirrors.pku.edu.cn/anaconda/archive/Anaconda3-2022.05-Linux-x86_64.sh -O ~/anaconda.sh && \
        /bin/bash ~/anaconda.sh -b -p /opt/conda && \
        rm ~/anaconda.sh && \
        ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
        echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
        find /opt/conda/ -follow -type f -name '*.a' -delete && \
        find /opt/conda/ -follow -type f -name '*.js.map' -delete && \
        /opt/conda/bin/conda clean -afy

# set path to conda
ENV PATH /opt/conda/bin:$PATH


# setup conda virtual environment
COPY ./requirements.txt /tmp/requirements.txt

RUN conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/ && conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/ && conda config --set show_channel_urls yes

RUN conda update conda \
    && conda env create --name voice-gen -f /tmp/requirements.txt
ENTRYPOINT ["python", "/var/www/run.py"]
EXPOSE 8000