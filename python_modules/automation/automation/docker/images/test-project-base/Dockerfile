####################################################################################################
#
# DAGSTER BUILDKITE TEST IMAGE BUILDER BASE
#
# We use this Dockerfile to build the base image for the test Dagster project
# image that is built in our CI pipeline.
#
####################################################################################################
ARG BASE_IMAGE
ARG PYTHON_VERSION
FROM "${BASE_IMAGE}" AS snapshot_builder

RUN apt-get update -yqq \
    && apt-get install -yqq \
    build-essential \
    cron \
    g++ \
    gcc \
    git \
    make

RUN pip install -U uv
RUN git clone --depth 1 https://github.com/dagster-io/dagster.git \
    && cd dagster \
    && python -m uv pip install \
    -e python_modules/dagster \
    -e python_modules/dagster-pipes \
    -e python_modules/libraries/dagster-shared \
    -e python_modules/dagster-graphql \
    -e python_modules/dagster-webserver \
    -e python_modules/libraries/dagster-celery[flower,redis,kubernetes] \
    -e python_modules/libraries/dagster-postgres \
    -e python_modules/libraries/dagster-pandas \
    -e python_modules/libraries/dagster-aws \
    -e python_modules/libraries/dagster-gcp \
    -e python_modules/libraries/dagster-k8s \
    -e python_modules/libraries/dagster-docker \
    -e python_modules/libraries/dagster-celery-k8s \
    && pip freeze --exclude-editable > /snapshot-reqs.txt

FROM "${BASE_IMAGE}"

COPY --from=snapshot_builder /snapshot-reqs.txt .

# gcc etc needed for building gevent
RUN apt-get update -yqq \
    && apt-get install -yqq \
    build-essential \
    cron \
    g++ \
    gcc \
    git \
    make

RUN pip install -U uv
RUN python -m uv pip install -r /snapshot-reqs.txt

# New versions of debian require allowlisting folders where `git` can run
RUN git config --system --add safe.directory \*
