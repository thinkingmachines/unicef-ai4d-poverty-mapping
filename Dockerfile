FROM python:3.9.16
ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"
COPY environment.yml .
COPY requirements.txt .
COPY pyproject.toml .
COPY setup.cfg .
COPY setup.py .
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh \
    && echo "Running $(conda --version)" && \
    conda init bash && \
    . /root/.bashrc && \
    conda update conda && \
    conda env create --prefix ./env -f environment.yml --no-default-packages && \
    conda activate ./env && \
    conda install -c conda-forge gdal -y && \
    pip install -r requirements.txt && \
    pip install -e . && \
    echo 'import geopandas;print("Hello World!")' > python-app.py
RUN echo 'conda activate ./env \n\
alias python-app="python python-app.py"' >> /root/.bashrc
ENTRYPOINT [ "/bin/bash", "-l", "-c" ]
CMD ["python python-app.py"]