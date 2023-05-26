FROM python:3.9.16
ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"
WORKDIR /root/povmap
COPY povertymapping/ povertymapping/
COPY notebooks/ notebooks/
COPY scripts/ scripts/
COPY environment.yml .
COPY requirements.txt .
COPY pyproject.toml .
COPY setup.cfg .
COPY setup.py .
COPY LICENSE .
COPY README.md .
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
    pip install -e . 
RUN echo 'conda activate ./env \n\
alias run-rollout="python scripts/run_rollout.py"' >> /root/.bashrc
ENTRYPOINT [ "/bin/bash", "-l", "-c" ]
EXPOSE 8888
RUN mkdir -p /root/povmap/data &&\
 mkdir -p /root/povmap/output-notebooks &&\
 mkdir -p /root/.eog_creds &&\
 mkdir -p /root/.geowrangler &&\
 mkdir -p /root/.cache &&\
 ln -s /root/.geowrangler /root/.cache/geowrangler
VOLUME /root/povmap/data /root/povmap/output-notebooks /root/.eog_creds /root
# CMD ["python scripts/run_rollout.py"]
CMD ["jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"]
