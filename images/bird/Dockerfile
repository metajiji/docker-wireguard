FROM alpine:3.16

RUN apk add --no-cache --upgrade \
        gettext \
        ncurses-libs \
        readline

ENV BIRD_VERSION=2.0.10
RUN apk add --no-cache --upgrade --virtual .build-deps \
        autoconf \
        bison \
        ca-certificates \
        flex \
        g++ \
        gcc \
        linux-headers \
        make \
        ncurses-dev \
        readline-dev \
    && mkdir -vp \
        /etc/bird \
        /tmp/bird \
    && wget -O- https://bird.network.cz/download/bird-$BIRD_VERSION.tar.gz \
        | tar -xzf- --strip-components=1 -C /tmp/bird \
    && (cd /tmp/bird \
        && autoconf \
        && autoheader \
        && ./configure \
        && make -j$(nproc) \
        && make install) \
    && rm -rf /tmp/bird \
    && apk del .build-deps

COPY docker-entrypoint.sh /
COPY bird.conf.template /etc/bird-templates/

VOLUME /etc/bird

EXPOSE 179

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["bird", "-f", "-c", "/etc/bird/bird.conf"]
