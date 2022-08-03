FROM alpine:3.16

RUN apk add --no-cache --upgrade \
        wireguard-tools

COPY docker-entrypoint.sh /

CMD /docker-entrypoint.sh
