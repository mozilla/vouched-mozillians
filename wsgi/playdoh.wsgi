import os
import site

from django.core.wsgi import get_wsgi_application  # noqa

try:
    import newrelic.agent
except ImportError:
    newrelic = False


if newrelic:
    newrelic_ini = os.getenv('NEWRELIC_PYTHON_INI_FILE', False)
    if newrelic_ini:
        newrelic.agent.initialize(newrelic_ini)
    else:
        newrelic = False

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mozillians.settings')

# Add `mozillians` to the python path
wsgidir = os.path.dirname(__file__)
site.addsitedir(os.path.abspath(os.path.join(wsgidir, '../')))

application = get_wsgi_application()

if newrelic:
    application = newrelic.agent.wsgi_application()(application)
