import logging
import os
import uuid

from django.http import HttpResponse
from django.template import Context
from django.template import Template
from django.conf import settings

from apps.models import App

logger = logging.getLogger(__name__)


def index(request):
    page_title = 'LLMStack: No-code platform to build generative AI apps, chatbots and agents with your data.'
    if request.path.startswith('/app/'):
        app_id = request.path.split('/')[2]
        try:
            app = App.objects.get(published_uuid=uuid.UUID(app_id))
            page_title = app.name + ' | LLMStack'
        except App.DoesNotExist:
            pass

    with open(os.path.join(settings.REACT_APP_DIR, 'build', 'index.html')) as f:
        template = Template(f.read())
        context = Context(
            {'page_title': page_title},
        )
        return HttpResponse(template.render(context=context))
