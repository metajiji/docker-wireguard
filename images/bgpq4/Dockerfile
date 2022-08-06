FROM alpine:3.16

RUN apk add --no-cache --upgrade \
        git \
        python3

ENV BGPQ4_VERSION=1.5
RUN apk add --no-cache --upgrade --virtual .build-deps \
        autoconf \
        automake \
        file \
        g++ \
        libtool \
        make \
    && mkdir -v /tmp/bgpq4 \
    && wget -O- https://github.com/bgp/bgpq4/tarball/$BGPQ4_VERSION \
        | tar -xzf- --strip-components=1 -C /tmp/bgpq4 \
    && (cd /tmp/bgpq4 \
        && ./bootstrap \
        && ./configure \
        && make -j$(nproc) \
        && make install) \
    && rm -rf /tmp/bgpq4 \
    && apk del .build-deps

ENV PATH=/tools-venv/bin:$PATH
COPY requirements.txt /tools/requirements.txt
RUN python3 -m venv /tools-venv \
    && pip install -U \
        -r /tools/requirements.txt

COPY tools /tools
