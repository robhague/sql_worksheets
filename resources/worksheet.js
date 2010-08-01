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

/*
 * Textarea autoresizer code adapted from: 
 *   http://www.sitepoint.com/blogs/2009/07/29/build-auto-expanding-textarea-1/
 */
var resize_text_area = function() {
		var hCheck = !($.browser.msie || $.browser.opera);

		// resize a textarea
		return function() {
			// find content length and box width
			var vlen = this.value.length, ewidth = this.offsetWidth;
			if (vlen != this.valLength || ewidth != this.boxWidth) {

				if (hCheck && (vlen < this.valLength || ewidth != this.boxWidth)) {
            this.style.height = "0px";
        }
				var h = this.scrollHeight;

				this.style.overflow = "hidden";
				this.style.height = h + "px";

				this.valLength = vlen;
				this.boxWidth = ewidth;
			}

			return true;
		};
}();


/**
 * Process a given block
 */
function process_block(blockID) {
    var query = $('#block'+blockID+' > .query').val();
    if (query[0] == '?') {
        // SQL query
        ajax_request('.', 'sql_query='+encodeURIComponent(query.substring(1)),
                     receive_response(blockID));
    } else {
        // Plain text
        addBlockAfter(blockID);
    }
}

/**
 * Add a new query block
 */
var add_query = function() {
    var nextID = 1;
    return function(afterSelector) {
        $(afterSelector).after('<div class="block" id="block'+nextID+'"><textarea class="query" rows="1" onchange="process_block('+nextID+')"></textarea><div class="answer"></div></div>');
				$('#block'+nextID+' > .query').bind("keyup", resize_text_area)
            .bind("focus", resize_text_area);
        $('#block'+nextID+' > .query').focus();
        nextID++;
    }
}();

function addBlockAfter(blockID) {
  var afterID = blockID+1;
  if ($('#block'+afterID).length == 0) {
    add_query('#block'+blockID);
  }
}

/**
 * Update a block with the repsonse to a query
 */
function receive_response(blockID) {
    return function(answerJSON) {
        var blockElement = $('#block'+blockID);
        var queryElement = $('#block'+blockID+' > .query');
        var answerElement = $('#block'+blockID+' > .answer');
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
            blockElement.removeClass('error');
            blockElement.addClass('value');
            
            addBlockAfter(blockID);
        } else {
            answerElement.text(String(answer['error']));
            blockElement.removeClass('value');
            blockElement.addClass('error');
            queryElement.focus();
        }
    };
}