FROM  rabbitmq

RUN mkdir -p /etc/rabbitmq/conf.d
RUN chown -R rabbitmq:rabbitmq /etc/rabbitmq/conf.d
COPY 20-logging.conf /etc/rabbitmq/conf.d

EXPOSE 4369 5671 5672 15671 15672 15692 25672 35672-35682
