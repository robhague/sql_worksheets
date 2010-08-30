# Development notes for Worksheets

## Modification-free updates

The eventual plan is that, instead of updating a block in place, changing a block will create a new row in the table with the same blockid, but a greater seq. In order to get the current view of the document, we select the row with the highest seq for each blockid. This is slightly hampered by the fact that SQLite doesn't support multiple columns for WHERE... IN... clauses (my SQL book suggests that it should, but that's academic). Fortunately, we can work around this using views:

     CREATE VIEW current AS
       SELECT blockid, MAX(seq) AS seq
       FROM blocks GROUP BY blockid;

A natural join between this view and the current table than gives the correct subset of rows.
