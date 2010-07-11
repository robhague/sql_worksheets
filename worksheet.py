#!/usr/bin/env python
#
# SQL Worksheets - a simple interface for querying databases
# (c) 2010 Rob Hague

import re, BaseHTTPServer, optparse, sys
from urlparse import urlparse, parse_qs

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


def worksheet_handler(db, options):
    """Create a worksheet request handler class, closed over a DB and
    an object representing command line options."""

    class WorksheetRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        """A HTTP request handler to display an SQL worksheet"""

        def allow_request(self):
            if self.client_address[0] in options.accept:
                return 1
            else:
                self.start_response(403, 'Forbidden', 'text/plain')
                self.wfile.write("This server cannot be accessed remotely.")
                return 0

        def do_GET(self):
            """Respond to a single HTTP request; called by the HTTP server"""

            if self.allow_request():
                params = parse_qs(urlparse(self.path).query)
                
                if params.has_key('resource'):
                    filename = params['resource'][0]
                    if re.match('^[A-Za-z._-]*$', filename):
                        self.start_response(200, 'OK', 'text/plain')
                        self.wfile.write(open('resources/'+filename).read());
                    else:
                        self.start_response(404, 'Not found', 'text/html')
                        self.wfile.write(not_found_HTML % {'resource': filename})
                else:
                    self.start_response(200, 'OK', 'text/html')
                    self.wfile.write(self.generate_base_page(self.path, params))

        def do_POST(self):
            if self.allow_request():
                content_length = int(self.headers['Content-length'])
                post_params = parse_qs(self.rfile.read(content_length))        
            if post_params.has_key('sql_query'):
                self.start_response(200, 'OK', 'text/plain')
                self.wfile.write(to_JSON(db.query(post_params['sql_query'])))
            else:
                self.start_response(404, 'Not Found', 'text/plain')
                self.wfile.write(not_found_HTML % {'resource': self.path})
                
        def start_response(self, code, msg, content_type):
            self.send_response(code, msg)
            self.send_header('Content-type', content_type)
            self.end_headers()

        def generate_base_page(self, path, params):
            """Generate the initial HTML page"""
            return base_page_HTML % {'title': db.title()}

    return WorksheetRequestHandler 

def start_worksheet_server(DbClass, args):
    """Start a worksheet server of the given class"""

    # Parse arguments
    parser = optparse.OptionParser()
    parser.add_option('-p', '--port', type='int', default=8000)
    parser.add_option('-a', '--accept', action='append', default=['127.0.0.1'])
    (options, args) = parser.parse_args(args[1:])

    # Create a database, passing in the remaining arguments
    try:
        db = DbClass(*args)
    except Exception as e:
        print 'Cannot instantiate DB: '+str(e)
        exit(2)

    # Start the HTTP server
    print 'Serving on port '+str(options.port)+'...'
    server_address = ('', options.port)
    httpd = BaseHTTPServer.HTTPServer(server_address,
                                      worksheet_handler(db, options))
    httpd.serve_forever()

# If the script is run directly, explain that a driver file is necessary
if __name__ == '__main__':
    print 'Use a driver file; see documentation.'
