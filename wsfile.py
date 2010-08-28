#!/usr/bin/env python
# (c) Rob Hague 2010 rob@rho.org.uk
#
# Facilities for reading and writing Worksheet files. This file may
# either be imported as a module, or called as a standalone script.
#
# A worksheet consists of a directory containing an SQLite database
# file, WORKSHEET, and potentially other collaterals. The schema of
# the database is as follows:
#
# Table "blocks":
#   blockid (Primary key): The numeric ID of the block, assigned sequentially
#                          by the front end as blocks are created.
#   seq: An integer, currently unused but intended to support undo.
#   query: Text of the query part of this block
#   answer: Text of the answer part of this block

import os, os.path, sqlite3, sys

class WorksheetStorage:
    'A class representing the on-disk storage of a worksheet.'
    def __init__(self, dirname):
        self.dbFilename = os.path.join(dirname, 'WORKSHEET')
        self.conn = sqlite3.connect(self.dbFilename)

    def __del__(self):
        try:
            self.conn.close()
        except:
            pass

    def sql(self, *args):
        'Utility method used to execute SQL on the Worksheet database'
        self.conn.execute(*args)
        self.conn.commit()

    def serialise(self, target):
        'Serialise a worksheet'
        c = self.conn.cursor()
        target.write('{\n')
        c.execute('select * from blocks order by blockid')
        target.write('  "contents" : [')
        target.write(','.join(
                ['{ "blockid":"%d","seq":"%d","query":"%s","answer":%s}' %
                 (blockid, seq, query, answer)
                 for (blockid, seq, query, answer) in c]))
        target.write(']\n}\n')
        c.close()

    def update(self, blockid, query, answer):
        self.sql('''INSERT OR REPLACE
                    INTO blocks (blockid, seq, query, answer)
                    VALUES (?, ?, ?, ?)''', 
                  (blockid, 0, query, answer))
    @classmethod
    def create_worksheet(cls, dirname, force):
        'Set up a Worksheet'
        if os.path.exists(dirname):
            if not os.path.isdir(dirname):
                raise Exception(dirname+" is not a directory")
        else:
            os.makedirs(dirname)
        dbfilename = os.path.join(dirname, 'WORKSHEET')
        if os.path.exists(dbfilename):
            if force:
                os.remove(dbfilename)
            else:
                raise Exception('Worksheet already exists at '+dirname)
    
        worksheet = WorksheetStorage(dirname)
        worksheet.sql('''CREATE TABLE blocks (blockid int, seq int, query text,
                                              answer text,
                                              PRIMARY KEY (blockid, seq))''');
        return worksheet

if __name__ == '__main__':
    # Parse arguments
    import optparse
    import sys
    parser = optparse.OptionParser()
    parser.add_option('-c', '--create', action='store_true')
    parser.add_option('-f', '--force', action='store_true')
    parser.add_option('-s', '--serialise', action='store_true')

    (options, args) = parser.parse_args(sys.argv[1:])

    try:
        worksheetName = args[0]
        # Create the worksheet, if required. Otherwise, open it.
        if (options.create):
            worksheet = WorksheetStorage.create_worksheet(worksheetName,
                                                          options.force)
        else:
            worksheet = WorksheetStorage(worksheetName)

        # Serialise the worksheet to standard output
        if (options.serialise):
            worksheet.serialise(sys.stdout)

    except :
        print sys.exc_info()[1]
