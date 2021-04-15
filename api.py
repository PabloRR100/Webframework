# api.py

import os
import inspect

from jinja2 import Environment, FileSystemLoader
from parse import parse
from requests import Session as RequestsSession
from webob import Request  # , Response
from whitenoise import WhiteNoise
from wsgiadapter import WSGIAdapter as RequestsWSGIAdapter

from constants import BASE_URL
from middleware import Middleware
from response import Response


class API:
    def __init__(self, templates_dir="templates", static_dir="static"):
        self.routes = {}
        self.exception_handler = None
        self.templates_env = Environment(
            loader=FileSystemLoader(
                searchpath=os.path.abspath(templates_dir)
            )
        )
        self.whitenoise = WhiteNoise(
            application=self.wsgi_app,
            root=static_dir
        )
        self.middleware = Middleware(self)

    def __call__(self, environ, start_response):
        """ We need to distinguish if the request if for static files and use
        WhiteNoise, or for data and use the Middleware
        """
        path_info = environ["PATH_INFO"]
        if path_info.startswith("/static"):
            environ["PATH_INFO"] = path_info[len("/static"):]
            return self.whitenoise(environ, start_response)
        return self.middleware(environ, start_response)

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.handle_request(request)
        return response(environ, start_response)

    def test_session(self, base_url=BASE_URL):
        session = RequestsSession()
        session.mount(prefix=base_url, adapter=RequestsWSGIAdapter(self))
        return session

    def add_middleware(self, middleware_cls):
        self.middleware.add(middleware_cls)

    @staticmethod
    def default_response(response):
        response.status_code = 404
        response.text = "Not found."

    def add_exception_handler(self, exception_handler):
        self.exception_handler = exception_handler

    def find_handler(self, request_path):
        """ Look for the corresponding handler for the incoming path """
        for path, handler_data in self.routes.items():
            parsed_result = parse(path, request_path)
            if parsed_result is not None:
                return handler_data, parsed_result.named
        return None, None

    def handle_request(self, request):

        response = Response()
        handler_data, kwargs = self.find_handler(request_path=request.path)

        try:
            if handler_data:
                handler = handler_data["handler"]
                allowed_methods = handler_data["allowed_methods"]
                if inspect.isclass(handler):
                    handler = getattr(handler(), request.method.lower(), None)
                    if handler is None:
                        raise AttributeError("Method not allowed", request.method)
                else:
                    if request.method.lower() not in allowed_methods:
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

    def add_route(self, path, handler, allowed_methods=None):
        assert path not in self.routes, "Such route already exists."
        if allowed_methods is None:
            allowed_methods = ["get", "post", "put", "patch", "delete", "options"]
        self.routes[path] = {"handler": handler, "allowed_methods": allowed_methods}

    def route(self, path, allowed_methods=None):
        if path in self.routes.keys():
            raise AssertionError("Duplicated route")

        def wrapper(handler):
            self.add_route(path, handler, allowed_methods)
            return handler

        return wrapper

    def template(self, template_name, context=None):
        context = {} or context
        return self.templates_env.get_template(
            name=template_name
        ).render(**context)

