# api.py

import os
import inspect

from jinja2 import Environment, FileSystemLoader
from parse import parse
from requests import Session as RequestsSession
from webob import Request, Response
from wsgiadapter import WSGIAdapter as RequestsWSGIAdapter

from constants import BASE_URL


class API:
    def __init__(self, templates_dir="templates"):
        self.routes = {}
        self.exception_handler = None
        self.templates_env = Environment(
            loader=FileSystemLoader(
                searchpath=os.path.abspath(templates_dir)
            )
        )

    def __call__(self, environ, start_response):
        request = Request(environ)

        response = self.handle_request(request)

        return response(environ, start_response)

    def test_session(self, base_url=BASE_URL):
        session = RequestsSession()
        session.mount(prefix=base_url, adapter=RequestsWSGIAdapter(self))
        return session

    @staticmethod
    def default_response(response):
        response.status_code = 404
        response.text = "Not found."

    def add_exception_handler(self, exception_handler):
        self.exception_handler = exception_handler

    def find_handler(self, request_path):
        """ Look for the corresponding handler for the incoming path """
        for path, handler in self.routes.items():
            parsed_result = parse(path, request_path)
            if parsed_result:
                return handler, parsed_result.named
        return None, None

    def handle_request(self, request):

        response = Response()
        handler, kwargs = self.find_handler(request_path=request.path)

        try:
            if handler:
                if inspect.isclass(handler):
                    handler = getattr(handler(), request.method.lower(), None)
                    if handler is None:
                        raise AttributeError("Method not allowed", request.method)
                handler(request, response, **kwargs)
            else:
                self.default_response(response)
        except Exception as e:
            if self.exception_handler is None:
                raise e
            else:
                self.exception_handler(request, response, e)
        return response

    def route(self, path):
        if path in self.routes.keys():
            raise AssertionError("Duplicated route")

        def wrapper(handler):
            self.routes[path] = handler
            return handler

        return wrapper

    def template(self, template_name, context=None):
        context = {} or context
        return self.templates_env.get_template(
            name=template_name
        ).render(**context)

