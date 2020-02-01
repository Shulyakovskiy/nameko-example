import yagmail
from dynaconf import settings
from nameko.events import event_handler, EventDispatcher
from nameko.rpc import rpc, RpcProxy
from nameko.timer import timer

if settings.DEBUG:
    print("Starting in DEBUG mode")
else:
    print("Starting in PRODUCTION mode")


class Mail(object):
    name = "mail"

    @rpc
    def send(self, to, subject, contents):
        if settings.DEBUG:
            print(
                u'Sending email "%s" to "%s" with contents "%s"'
                % (subject, to, contents)
            )
            return

        # email will be sent only if DEBUG=False in settings.py
        # or you do:
        #  export DYNACONF_DEBUG='@bool False'
        yag = yagmail.SMTP(settings.EMAIL, settings.PASSWORD)

        # Tip: export DYNACONF_EMAIL='myemail@gmail.com'
        #      export DYNACONF_PASSWORD='secret'
        yag.send(
            cc=to.encode("utf-8"),
            subject=subject.encode("utf-8"),
            contents=[contents.encode("utf-8")],
        )


class Compute(object):
    name = "compute"
    mail: RpcProxy = RpcProxy("mail")

    @rpc
    def compute(self, operation, value, other, email):
        operations = {
            u"sum": lambda x, y: int(x) + int(y),
            u"mul": lambda x, y: int(x) * int(y),
            u"div": lambda x, y: int(x) / int(y),
            u"sub": lambda x, y: int(x) - int(y),
        }
        try:
            result = operations[operation](value, other)
        except Exception as e:
            self.mail.send(email, "An error occurred", str(e))
            raise
        else:
            self.mail.send(
                email, "Your operation is complete!", "The result is: %s" % result
            )
            return result


class Service:
    name = "service"

    @timer(interval=1)
    def ping(self):
        # method executed every second
        print("pong")


class ServiceA:
    """ Event dispatching service. """

    name = "service_a"

    dispatch: EventDispatcher = EventDispatcher()

    @rpc
    def dispatching_method(self, payload):
        self.dispatch("event_type", payload)


class ServiceB:
    """ Event listening service. """

    name = "service_b"

    @event_handler("service_a", "event_type")
    def handle_event(self, payload):
        print("service b received:", payload)
