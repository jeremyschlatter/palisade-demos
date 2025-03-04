FROM alpine:latest
RUN apk add --no-cache bash
WORKDIR /app
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
CMD ["/app/entrypoint.sh"]
