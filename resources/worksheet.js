/**
 * Support functions for worksheets
 */

/**
 * Make an AJAX request, and process the result with the response function (if successful).
 */
function ajax_request(path, value, response) {
  var xmlhttp = new XMLHttpRequest();
  xmlhttp.open('POST', path, true);
  xmlhttp.onreadystatechange = function() {
    if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {  
      response(xmlhttp.responseText);
    }
  };
  xmlhttp.send(value);
}

/**
 * Send a query for a given block.
 */
function send_query(blockID) {
    query = $('#block'+blockID+' > .query').val();
    ajax_request('.', 'sql_query='+encodeURIComponent(query),
                 receive_response(blockID));
}

/**
 * Add a new query block
 */
var add_query = function() {
    var nextID = 1;
    return function(afterSelector) {
        $(afterSelector).after('<div class="sql_query" id="block'+nextID+'"><textarea class="query"></textarea> <input type="submit" value="=" onclick="send_query('+nextID+')" class="execute_query"><div class="answer"></div></div>');
        $('#block'+nextID+' > .query').focus();
        nextID++;
    }
}()

/**
 * Update a block with the repsonse to a query
 */
function receive_response(blockID) {
    return function(answerJSON) {
        queryElement = $('#block'+blockID+' > .query');
        answerElement = $('#block'+blockID+' > .answer');
        var answer = json_parse(answerJSON);
        if (answer['result']) {
            var result = '<table class="results"><tr>';
            for(var heading in answer['headings']) {
                result += '<th>'+answer['headings'][heading]+'</th>'
            }
            result += '</tr>'
            for(var row in answer['result']) {
                result += '<tr>';
                for(var column in answer['result'][row]) {
                    result += '<td>'+answer['result'][row][column]+'</td>';
                }
                result += '</tr>';
            }
            answerElement.html(result+'</table>');
            answerElement.removeClass('error');
            if ($('#block'+(blockID+1)).length == 0) {
                add_query('#block'+blockID);
            } else {
                $('#block'+afterID+' > .query').focus();
            }
        } else {
            answerElement.text(String(answer['error']));
            answerElement.addClass('error');
            queryElement.focus();
        }
    };
}