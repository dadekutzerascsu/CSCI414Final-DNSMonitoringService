FROM alpine:3.21

RUN apk add --no-cache apache2-utils curl iproute2 iputils bind-tools
CMD ["sleep", "infinity"]
