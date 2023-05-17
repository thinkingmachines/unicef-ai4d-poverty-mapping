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
    pip install papermill && \
    pip install -e . 
RUN echo 'conda activate ./env \n\
alias run-rollout="python scripts/run_rollout.py"' >> /root/.bashrc
ENTRYPOINT [ "/bin/bash", "-l", "-c" ]
CMD ["python scripts/run_rollout.py"]