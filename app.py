# app.py

from api import API

web_app = API(templates_dir="templates")


@web_app.route("/home")
def home(request, response):
    response.text = "Hello from the HOME page"
    response.body = web_app.template(
        "home.html",
        context={
            "title": "Awesome Framework",
            "name": "Bumbo"
        }
    )


@web_app.route("/about")
def about(request, response):
    response.text = "Hello from the ABOUT page"


@web_app.route("/hello/{name}")
def greeting(request, response, name):
    response.text = f"Hello {name}"


@web_app.route("/book")
class BooksResource:
    def get(self, req, resp):
        resp.text = "Books Page"

    def post(self, req, resp):
        resp.text = "Endpoint to create a book"


@web_app.route("/template")
def template_handler(req, resp):
    resp.body = web_app.template(
        "index.html",
        context={"name": "Bumbo", "title": "Best Framework"}
    ).encode()


@web_app.route("/exception")
def exception_throwing_handler(request, response):
    raise AssertionError("This handler should not be used.")


if __name__ == "__main__":

    web_app(environ={}, start_response=None)
