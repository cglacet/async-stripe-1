import json
from urllib.parse import urlencode
from tornado.httpclient import AsyncHTTPClient, HTTPError
from stripe.api_requestor import _api_encode
from async_stripe.patched_stripe import real_stripe


VERSION = "v1"
BASE_URL = "{}/{}/".format(real_stripe.api_base, VERSION)

client = AsyncHTTPClient()


class ResourceMetaclass(type):
    def __getattr__(cls, name):
        resource = getattr(real_stripe, cls.resource)
        return getattr(resource, name)


class AsyncBaseResource(metaclass=ResourceMetaclass):
    @classmethod
    async def fetch(cls, url, method='GET', data=None):
        headers = {}

        if 'idempotency_key' in data:
            headers['idempotency_key'] = data.pop('idempotency_key') 

        if data:
            body = urlencode(list(_api_encode(data)), doseq=True)
        else:
            body = None

        if method == 'GET' and body:
            url = '%s?%s' % (url, body)
            body = None # reset body for GET request

        try:
            response = await client.fetch(
                url,
                method=method,
                auth_username=real_stripe.api_key,
                headers=headers,
                body=body
            )
        except HTTPError as e:
            # :TODO: Raise stipe's exceptions
            if hasattr(e, 'response'):
                print('ERROR:', e.code)
                print(e.response.body)
            raise
        except Exception as e:
            # :TODO: Raise stipe's exceptions
            raise
        else:
            stripe_obj = real_stripe.util.convert_to_stripe_object(
                json.loads(response.body), real_stripe.api_key
            )
            return stripe_obj

    @classmethod
    async def retrieve(cls, id):
        url = cls.url + '/' + id
        stripe_obj = await cls.fetch(url)
        return stripe_obj

    @classmethod
    async def create(cls, **kwargs):
        url = cls.url
        stripe_obj = await cls.fetch(url, method='POST', data=kwargs)
        return stripe_obj

    @classmethod
    async def modify(cls, id, **kwargs):
        url = cls.url + '/' + id
        stripe_obj = await cls.fetch(url, method='POST', data=kwargs)
        return stripe_obj

    @classmethod
    async def delete(cls, id):
        url = cls.url + '/' + id
        stripe_obj = await cls.fetch(url, method='DELETE')
        return stripe_obj

    @classmethod
    async def list(cls, **kwargs):
        url = cls.url
        stripe_obj = await cls.fetch(url, data=kwargs)
        return stripe_obj

