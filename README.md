# Worksheets - a browser-based interface

Worksheets provide a simple browser-based interface to databases (and potentially other services). The user types queries into a text area, and the response is shown below. The worksheet provides a record of queries, and allows queries to be edited and resubmitted.

# Requirements

- Python 2.5 (or 2.4 with WSGIRef) or higher (but not Python 3.x)
- For SQLite databases, SQLite3 (included in Python 2.5 and higher)

# Running Worksheets

The worksheets script is not run directly; instead, each supported database type has an associated driver script. To start a server, run the driver script, passing the necessary information to specify the database  (for example, a filename or hostname). For example:

    sqlite_worksheet mydb.sqlite 8000

The above command line runs a server on port 8001, using the database file "mydb.sqlite" to respond to queries. To use the worksheet, visit the URL `http://localhost:8000`.

# Adding Support For New Database Types

To add support for a new database type, write a new driver script. This is a normal Python script that imports worksheet.py and calls the function `start_worksheet_server`, passing in a database object and optional port. The database object must implement the following methods:

- `title(self)`: Returns a page title, which should indicate the specific database being served
- `query(self, query)`: Runs the query string specified by the `query` parameter, and returns a dict containing the following keys:
  - In the case of success, `'headings` mapping to a list of column headings, and `result`, mapping to a list of rows, where each row is a list of values. The length of each row should be the same as that of the headings list.
  - In the case of error, `error` mapping to an error message.
  
The driver script `dummy_worksheet` provides a trivial example.
