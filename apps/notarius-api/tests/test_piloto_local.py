"""Run with --settings=config.settings_piloto; synthetic data only."""
from django.conf import settings
from django.test import SimpleTestCase
from apps.base.piloto import PilotoLocalMiddleware
from django.test import RequestFactory
from django.http import HttpResponse
from unittest import skipUnless


@skipUnless(getattr(settings, 'PILOTO_LOCAL', False), 'Requer --settings=config.settings_piloto')
class PerfilPilotoTests(SimpleTestCase):
    def test_profile_disables_debug_external_ai_and_public_storage(self):
        self.assertTrue(settings.PILOTO_LOCAL)
        self.assertFalse(settings.DEBUG)
        self.assertFalse(settings.USE_S3)
        self.assertFalse(settings.AI_GENERATION_ENABLED)
        self.assertFalse(settings.CORS_ALLOW_ALL_ORIGINS)
        self.assertEqual(settings.OPENAI_API_KEY, '')
        self.assertEqual(settings.ROOT_URLCONF, 'config.urls_piloto')

    def test_middleware_refuses_remote_clients_and_does_not_cache_local_responses(self):
        middleware = PilotoLocalMiddleware(lambda request: HttpResponse('ok'))
        factory = RequestFactory()
        self.assertEqual(middleware(factory.get('/', REMOTE_ADDR='192.0.2.1')).status_code, 403)
        response = middleware(factory.get('/', REMOTE_ADDR='127.0.0.1'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_pilot_has_no_public_media_registration_or_external_legacy_routes(self):
        self.assertEqual(self.client.get('/health/').status_code, 200)
        for path in ['/media/documento.txt', '/api/v1/auth/register/', '/admin/',
                     '/api/v1/ai/generate-minuta/', '/api/v1/workflow/']:
            self.assertEqual(self.client.get(path).status_code, 404)
