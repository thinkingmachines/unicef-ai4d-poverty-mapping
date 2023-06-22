FROM python:3.9.16
LABEL org.opencontainers.image.source=https://github.com/thinkingmachines/unicef-ai4d-poverty-mapping
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
    pip uninstall pygeos shapely -y && \
    pip install pygeos==0.12.0 shapely==1.8.4 --no-binary pygeos --no-binary shapely && \
    pip install -e . 
RUN echo 'conda activate ./env \n\
alias run-rollout="python scripts/run_rollout.py"' >> /root/.bashrc
ENTRYPOINT [ "/bin/bash", "-l", "-c" ]
EXPOSE 8888
RUN mkdir -p /root/povmap/data/cache/geowrangler &&\
 ln -s /root/povmap/data/cache/geowrangler /root/.geowrangler &&\
 ln -s /root/povmap/data/cache/geowrangler /root/.cache/geowrangler &&\  
 mkdir -p /root/povmap/data/output-notebooks &&\
 ln -s /root/povmap/data/output-notebooks /root/povmap/output-notebooks &&\
 mkdir -p /root/povmap/data/eog_creds &&\
 ln -s /root/povmap/data/eog_creds /root/.eog_creds
VOLUME /root/povmap/data
# CMD ["python scripts/run_rollout.py"]
CMD ["jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"]
