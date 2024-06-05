FROM python:3.11-slim
COPY . /app
RUN cd /app && \
    pip install --upgrade --no-cache-dir build && \
    python -m build --wheel -vvv

FROM python:3.11-slim
COPY --from=0 /app/dist/qsynth-0.1.0-py3-none-any.whl /tmp
COPY --from=0 /app/requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install /tmp/qsynth-0.1.0-py3-none-any.whl && \
    rm /tmp/qsynth-0.1.0-py3-none-any.whl && \
    rm /tmp/requirements.txt

RUN useradd --create-home --home-dir /data msynth
USER msynth

VOLUME /data
WORKDIR /data
ENTRYPOINT ["python", "-m", "qsynth"]
CMD ["--help"]