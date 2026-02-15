import importlib.util
import uuid
import os

TEST_MODULE_PATH = os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'count_visitors.py')

class FakeTable:
    def __init__(self, *, raise_exc=False, count=1):
        self.raise_exc = raise_exc
        self.count = count
        self.last_key = None

    def update_item(self, Key=None, UpdateExpression=None, ExpressionAttributeValues=None, ReturnValues=None):
        self.last_key = Key
        if self.raise_exc:
            raise Exception('simulated dynamo failure')
        return {'Attributes': {'visitor_count': self.count}}


def load_module_unique():
    name = f"count_visitors_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, TEST_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_path_query_param():
    module = load_module_unique()
    event = {'queryStringParameters': {'page': '/about'}}
    assert module.get_path(event) == '/about'


def test_get_path_referer_header():
    module = load_module_unique()
    event = {'headers': {'referer': 'https://rmbh.me/index.html'}}
    assert module.get_path(event) == '/index.html'


def test_get_path_fallback_and_root():
    module = load_module_unique()
    # empty event -> /index
    assert module.get_path({}) == '/index'
    # explicit root page -> becomes /index
    assert module.get_path({'queryStringParameters': {'page': '/'}}) == '/index'


def test_lambda_handler_success(monkeypatch):
    module = load_module_unique()
    fake = FakeTable(count=42)
    # patch module.table
    module.table = fake

    event = {'queryStringParameters': {'page': '/mypage'}}
    resp = module.lambda_handler(event, None)

    assert resp['statusCode'] == 200
    assert 'Access-Control-Allow-Origin' in resp['headers']
    assert resp['body'] == '42'
    # ensure the table was called with the expected key
    assert fake.last_key == {'path_id': '/mypage'}


def test_lambda_handler_exception(monkeypatch):
    module = load_module_unique()
    fake = FakeTable(raise_exc=True)
    module.table = fake

    event = {}
    resp = module.lambda_handler(event, None)

    assert resp['statusCode'] == 200
    assert resp['body'] == '-'
