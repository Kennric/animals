import os
import urlparse
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.utils import redirect
from werkzeug.formparser import parse_form_data
from jinja2 import Environment, FileSystemLoader
import MySQLdb


def FetchOneAssoc(cursor):
    data = cursor.fetchone()
    if data == None :
        return None
    desc = cursor.description

    dict = {}

    for (name, value) in zip(desc, data) :
        dict[name[0]] = value

    return dict

class Animals(object):

    def __init__(self):
       
        self.db_user = os.environ['ANIMALS_DB_USER']
        self.db_pass = os.environ['ANIMALS_DB_PASS']
        self.db_host = os.environ['ANIMALS_DB_HOST']
        self.db_name = os.environ['ANIMALS_DB_NAME']


        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                 autoescape=True)

        self.url_map = Map([
            Rule('/', endpoint='take_quiz'),
            Rule('/<result_id>', endpoint='get_results')
        ])

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except HTTPException, e:
            return e


    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)


    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype='text/html')

        
    def insert_result(self, animal_id, caption_id):
        db = MySQLdb.connect(user=self.db_user, host=self.db_host, db=self.db_name, passwd=self.db_pass)
        db.autocommit(True)
        cursor = db.cursor() 
        sql = "INSERT INTO results (animal_id, caption_id) VALUES (%s, %s)"
        cursor.execute(sql, (animal_id, caption_id))
        result_id = cursor.lastrowid
        cursor.close()
        db.close()
        return result_id


    def on_take_quiz(self, request):
        db = MySQLdb.connect(user=self.db_user, host=self.db_host, db=self.db_name, passwd=self.db_pass)
        db.autocommit(True)
        cursor = db.cursor()

        if request.method == 'POST':

            animal_sql = "SELECT id FROM animals ORDER BY RAND() LIMIT 0,1;"
            caption_sql = "SELECT id FROM captions ORDER BY RAND() LIMIT 0,1;"

            cursor.execute(animal_sql)
            animal_id = cursor.fetchone()
            cursor.execute(caption_sql)
            caption_id = cursor.fetchone()
            cursor.close()

            result_id = self.insert_result(animal_id, caption_id)
        
            return redirect('/%s' % result_id)

        # not post, so select a random question to ask

        question_sql = "SELECT question FROM `questions` ORDER BY RAND() LIMIT 0,1;"
        cursor.execute(question_sql)
        question = cursor.fetchone()
        cursor.close()
        db.close()

        return self.render_template('quiz.html', question=question)


    def on_get_results(self, request, result_id):
        db = MySQLdb.connect(user=self.db_user, host=self.db_host, db=self.db_name, passwd=self.db_pass)
        db.autocommit(True)

        cursor = db.cursor()
        # look up the result, fetch the animal and caption
        result_sql = "SELECT animals.*, captions.caption, results.* \
                      FROM results \
                      JOIN captions ON results.caption_id = captions.id \
                      JOIN animals ON results.animal_id = animals.id \
                      WHERE results.id = %s"

        cursor.execute(result_sql, (result_id,))

        result = FetchOneAssoc(cursor)

        cursor.close()
        db.close()

        if result is None:
            return NotFound(description=None, response=None)

        return self.render_template('result.html', result=result)


def create_app(with_static=True):
    app = Animals()
    if with_static:
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/static':  os.path.join(os.path.dirname(__file__), 'static')
        })
    return app


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    app = create_app()
    run_simple('0.0.0.0', 5000, app, use_debugger=True, use_reloader=True)

