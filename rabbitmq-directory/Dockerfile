FROM rabbitmq:3-management

# Define environment variables.
# Probably not necessary, but for remote access you can't use guest account
# with rabbitmq. I made this when trying to troubleshoot things, might as well keep it in.

ENV RABBITMQ_USER test
ENV RABBITMQ_PASSWORD test
ENV RABBITMQ_PID_FILE /var/lib/rabbitmq/mnesia/rabbitmq

# Add scrip that will create a new user

ADD init.sh /init.sh
RUN chmod +x /init.sh

# Expose ports

EXPOSE 15672
EXPOSE 15671

# Execute the script

CMD ["/init.sh"]
