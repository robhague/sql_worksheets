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
 * Index page functions.
 */

function substring_match(term) {
    return function() { return $(this).text().indexOf(term) == -1; };
}

function inverse(fn) {
    return function() { return !fn.apply(this, arguments); };
}

function check_worksheet_name(name) {
    return /^[-\w]+(:?\/[-\w]+)*$/.exec(name);
}

function search_term_changed(event, value) {
    filter_items(event, value, '.index_entry', open_or_create);
    $('#create').attr('disabled', !check_worksheet_name(value));
}

function filter_items(event, term, item_selector, accept) {
    $(item_selector).show().filter(substring_match(term)).hide();
    if (event.keyCode == 13 && accept) {
        accept(item_selector, term);
    }
}

function open_or_create(selector, term) {
    var items = $(selector).filter(inverse(substring_match(term)));
    if (items.length == 0 && check_worksheet_name(term)) {
        $('#create').focus();
    } else if (items.length == 1) {
        window.location = items.find('> a')[0].href;
    }
}

function create_worksheet() {
    var term = $('#search').val();
    var url = window.location+term;
    jQuery.ajax({
        type: 'POST', url: url, data: { action: 'create' },
        success: function() { window.location = url; },
        error: function(xhr) { alert(xhr.responseText); }
    });
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

function query_changed() {
    var query = this.value;
    var blockElement = $(this.parentNode);

    // Reset class back to default
    blockElement
        .removeClass('b-header b-remotequery b-localquery b-text')
        .addClass('block');

    // Update the class according to the first character
    switch (query[0]) {
    case '#': // Header
        blockElement.addClass('b-header'); break;
    case '?': // SQL query
        blockElement.addClass('b-remotequery'); break;
    case '=': // JavaScript query
        blockElement.addClass('b-localquery'); break;
    default:  // Plain text
        blockElement.addClass('b-text');
    }
    resize_text_area.apply(this);
}

/**
 * Process a given block
 */
function process_block(blockID) {
    var blockElement = $('#block'+blockID);
    var queryElement = blockElement.find('> .query');
    var answerElement = blockElement.find('> .answer');
    var query = queryElement.val();
    var answer = {};

    // Javascript expression
    if (query[0] =='=') {
        try {
            answer['status'] = 'OK';
            answer['value'] = eval(query.substring(1));
            blockElement.addClass('value');
        } catch (e) {
            answer['status'] = 'error';
            answer['value'] = ''+e;
            blockElement.addClass('error');
        }
    }

    update_block(answer, blockElement);

    var answerString = JSON.stringify(answer);

    var params =
        'action=update&block=' + blockID +
        '&query=' + encodeURIComponent(query) +
        '&answer=' + encodeURIComponent(answerString);
    ajax_request(window.location, params, receive_response(blockID));

    addBlockAfter(blockID);
}

/**
 * Add a new query block
 */
var add_query = function() {
    var nextID = 1;
    return function(afterSelector, query, answer) {
        $(afterSelector).after('<div class="block" id="block'+nextID+'"><textarea class="query" rows="1" onchange="process_block('+nextID+')"></textarea><div class="answer"></div></div>');
				$('#block'+nextID+' > .query')
            .bind("keyup", query_changed)
            .bind("focus", query_changed)
            .html(query);
        var newSelector = '#block'+nextID;
        $(newSelector+' > .query').focus();
        if (answer) {
            update_block(answer, $(newSelector));
        }
        nextID++;
        return newSelector;
    };
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
        var answer = jQuery.parseJSON(answerJSON);
        update_block(answer, blockElement);
    };
}

function update_block(answer, blockElement)
{
    var answerElement = $(blockElement).find('> .answer');
    if (answer['headings']) {
        var result = '<table class="results"><tr>';
        for(var heading in answer['headings']) {
            result += '<th>'+answer['headings'][heading]+'</th>';
        }
        result += '</tr>';
        for(var row in answer['value']) {
            result += '<tr>';
            for(var column in answer['value'][row]) {
                result += '<td>'+answer['value'][row][column]+'</td>';
            }
            result += '</tr>';
        }
        answerElement.html(result+'</table>');
    } else if (answer['value']) {
        answerElement.text(String(answer['value']));   
    }

    switch (answer['status']) {
    case 'OK':
        blockElement.removeClass('error');
        blockElement.addClass('value');
        break;
    case 'error':
        blockElement.removeClass('value');
        blockElement.addClass('error');
        $(blockElement).find('> .query').focus();
        break;
    }
}

function initialise(path) {
    ajax_request(path, 'action=init',function(initial_doc) {
            var nextId = '#top';
            var initial_json = jQuery.parseJSON(initial_doc);
            var contents = initial_json['contents'];
            for(var i = 0; i < contents.length; i++) {
                var item = contents[i];
                nextId = add_query(nextId, item.query, item.answer);
            }
            add_query(nextId);
        });
}