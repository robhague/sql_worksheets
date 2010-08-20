#!/usr/bin/env python
#
# SQL Worksheets - a simple interface for querying databases
# (c) 2010 Rob Hague

from wsfile import WorksheetStorage
import re, BaseHTTPServer, optparse, sys, config, os
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
  <body onload="initialise('%(path)s')">
    <div class="watermark">Worksheet %(path)s</div>
    <div class="title">%(title)s</div>
    <a id="top"></a>

    <a id="bottom"></a>
    <!-- There needs to be a link at the bottom of the page, to catch
    the input focus as it leaves the last block. Note that this
    doesn't work on Safari or Chrome, so is only a temporary
    solution. -->
    <a href=".">Reload</a>
  </body>
</html>
"""

not_found_HTML = """<html>
  <head>
    <title>Resouce not found: %(resource)s</title>
  </head>
  <body>
    <h1>Resource Not Found</h1>
    <p>The resource %(resource)s could not be found.</p>
  </body>
</html>
"""

# Regular expressions
worksheet_path_RE = re.compile(r'^(/[-\w]+)+/?$')

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

    worksheets = {}
    def find_worksheet(path):
        ''''Return the worksheet object for the given path, creating
        it if necessary.'''
        if not worksheets.has_key(path):
            worksheets[path] = WorksheetStorage(path)
            print 'Opened worksheet %s' % path
        return worksheets[path]

    class WorksheetRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        """A HTTP request handler to display an SQL worksheet"""

        def allow_request(self):
            # Check request originates from a permitted host
            if self.client_address[0] not in options.accept:
                self.start_response(403, 'Forbidden',
                                    {'Content-type' : 'text/plain'})
                self.wfile.write("This server cannot be accessed remotely.")
                return 0
            
            # Check authentication if necessary
            if (options.basic_auth):
                if self.headers.has_key('Authorization'):
                    auth = self.headers['Authorization'].split(' ',1)
                    target = (config.login+':'+config.password)
                    target = target.encode('base64').strip()
                    if (len(auth) == 2 and auth[0] == 'Basic' and
                        auth[1] == target):
                        return 1
                    
                self.start_response(
                    401, 'Authorization Required',
                    {'Content-type': 'text/plain',
                     'WWW-Authenticate': 'Basic realm="Worksheet"'})
                return 0

            # OK
            return 1

        def do_GET(self):
            """Respond to a single HTTP request; called by the HTTP server"""

            if self.allow_request():
                url = urlparse(self.path)
                params = parse_qs(url.query)
                
                if params.has_key('resource'):
                    filename = params['resource'][0]
                    if re.match('^[A-Za-z._-]*$', filename):
                        filepath = os.path.join(os.path.dirname(sys.argv[0]),
                                                'resources', filename)
                        self.start_response(200, 'OK',
                                            {'Content-type': 'text/plain'})
                        self.wfile.write(open(filepath).read());
                    else:
                        self.not_found()
                elif url.path == '/':
                    self.start_response(200, 'OK',
                                        {'Content-type': 'text/html'})
                    self.generate_index_page(self.wfile)
                elif worksheet_path_RE.match(url.path):
                    self.start_response(200, 'OK',
                                        {'Content-type': 'text/html'})
                    self.wfile.write(self.generate_base_page(self.path, params))
                else:
                    self.not_found()

        def do_POST(self):
            if self.allow_request():
                content_length = int(self.headers['Content-length'])
                post_params = parse_qs(self.rfile.read(content_length))        
            if post_params.has_key('sql_query'):
                self.start_response(200, 'OK',
                                    {'Content-type': 'text/plain'})
                self.wfile.write(to_JSON(db.query(post_params['sql_query'])))
            elif (worksheet_path_RE.match(self.path) and
                  post_params.has_key('init')):
                try:
                    ws_file_path = os.path.expanduser(options.dir+self.path)
                    worksheet = find_worksheet(ws_file_path)
                    self.start_response(200, 'OK',
                                        {'Content-type': 'text/plain'})
                    worksheet.serialise(self.wfile)
                except:
                    print sys.exc_info()[1]
                    self.not_found()
            else:
                self.not_found()
                
        def start_response(self, code, msg, headers):
            self.send_response(code, msg)
            for (k,v) in headers.items():
                self.send_header(k,v)
            self.end_headers()

        def not_found(self):
            self.start_response(404, 'Not Found',
                                {'Content-type': 'text/html'})
            self.wfile.write(not_found_HTML % {'resource': self.path})
            
        def generate_base_page(self, path, params):
            'Generate the initial HTML page'
            return base_page_HTML % {'title': db.title(), 'path': self.path}

        def generate_index_page(self, target):
            'Write out an index page for the served directory.'
            target.write('<i>Index not yet implemented...</i>')

    return WorksheetRequestHandler 

def start_worksheet_server(DbClass, args):
    """Start a worksheet server of the given class"""

    # Parse arguments
    parser = optparse.OptionParser()
    parser.add_option('-p', '--port', type='int', default=8000)
    parser.add_option('-a', '--accept', action='append', default=['127.0.0.1'])
    parser.add_option('-b', '--basic-auth', action="store_true")
    parser.add_option('-d', '--dir', default='.')
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
