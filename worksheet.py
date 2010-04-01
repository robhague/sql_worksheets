#!/usr/bin/env python
#
# SQL Worksheets - a simple interface for querying databases
# (c) 2010 Rob Hague

import re
from cgi import parse_qs
from wsgiref.simple_server import make_server

# HTML templates
base_page_HTML = """<html>
  <head>
    <title>%(title)s</title>
    <script type="text/javascript" src="?resource=jquery.js"></script>
    <script type="text/javascript" src="?resource=json_parse.js"></script>
    <script type="text/javascript" src="?resource=worksheet.js"></script>
    <link rel="stylesheet" type="text/css" href="?resource=worksheet.css">
  </head>
  <body onload="add_query('#top')">
    <div class="watermark">Worksheet</div>
    <div class="title">%(title)s</div>
    <a id="top">
  </body>
</html>
"""

not_found_HTML = """<html>
  <head>
    <title>Resouce not found: %(resource)s</title>
  </head>
  <body>
    <center>
      <h1>Resource Not Found</h1>
      <p>The resource %(resource)s could not be found.
    </center>
  </body>
</html>
"""

# Simple JSON generation, as the json module is not included in older
# versions of Python.
def to_JSON(obj):
    """Simple JSON conversion"""
    if isinstance(obj, dict):
        return '{'+', '.join([str_JSON(K)+' : '+to_JSON(V)
                              for (K,V) in obj.items()])+'}'
    elif hasattr(obj, '__iter__'):
        return '['+', '.join([to_JSON(X) for X in obj])+']'
    else:
      return str_JSON(obj)

def str_JSON(obj):
    """Produce a representation of an object as a JSON string,
    escaping special characters."""
    return '"'+re.sub(r'[\\"]', r'\\\g<0>', str(obj))+'"'

class WorksheetApp:
    """A WSGI application to display an SQL worksheet"""
    def __init__(self, db):
        self.db = db

    def __call__(self, environ, start_response):
        """Respond to a single HTTP request; called by WSGI"""
        path = environ['PATH_INFO']
        params = parse_qs(environ.get('QUERY_STRING', ''))
        content_length = int('0'+environ['CONTENT_LENGTH'])
        post_params = parse_qs(environ['wsgi.input'].read(content_length))
        
        if params.has_key('resource'):
            filename = params['resource'][0]
            if re.match('^[A-Za-z._-]*$', filename):
                start_response('200 OK', [('Content-type', 'text/plain')])
                return open('resources/'+filename).read();
            else:
                start_response('404 Not found', [('Content-type','text,html')])
                return not_found_HTML % {'resource': filename }
        if post_params.has_key('sql_query'):
            start_response('200 OK', [('Content-type', 'text/json')])
            return to_JSON(self.db.query(post_params['sql_query']))
        else:
            start_response('200 OK', [('Content-type', 'text/html')])
            return self.generate_base_page(path, params)

    def generate_base_page(self, path, params):
        """Generate the initial HTML page"""
        return base_page_HTML % {'title': self.db.title()}

def start_worksheet_server(db, port = 8000):
    """Start a worksheet server on port 8000 with the given database object."""
    httpd = make_server('', int(port), WorksheetApp(db))
    print 'Serving on port '+str(port)+'...'
    httpd.serve_forever() # Serve until process is killed

# If the script is run directly, explain that a driver file is necessary
if __name__ == '__main__':
    print 'Use a driver file; see documentation.'
