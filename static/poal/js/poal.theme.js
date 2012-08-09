// Generated by CoffeeScript 1.3.3
(function() {
  var $;

  $ = jQuery;

  AjaxSolr.theme.prototype.result = function(doc, snippet) {
    var output;
    output = '<div><h5>' + doc.title + '</h5>';
    output += '<p id="links_' + doc.id + '" class="links"></p>';
    output += '<p>' + snippet + '</p></div>';
    return output;
  };

  AjaxSolr.theme.prototype.snippet = function(doc) {
    var output;
    output = '';
    output += '<span style="display:none;">' + JSON.stringify(doc);
    output += '</span> <a href="#" class="more">more</a>';
    return output;
  };

  AjaxSolr.theme.prototype.tag = function(value, num, weight, handler) {
    return $('<a href="#" class="tagcloud_item"/>').text(value + '(' + num + ')').addClass('tagcloud_size_' + weight).click(handler);
  };

  AjaxSolr.theme.prototype.simpletag = function(value, handler) {
    return $('<a href="#"/>').text(value).click(handler);
  };

  AjaxSolr.theme.prototype.facet_link = function(value, handler) {
    return $('<a href="#"/>').text(value).click(handler);
  };

  AjaxSolr.theme.prototype.facet_link_header = function(header, value, handler) {
    return $('<span class="bold"/>').text(header + ": ").append($('<a href="#"/>').text(value).click(handler));
  };

  AjaxSolr.theme.prototype.no_items_found = function() {
    return 'no items found in current selection';
  };

  AjaxSolr.theme.prototype.list_concat = function(list, items, separator) {
    var i, _i, _ref, _results;
    jQuery(list).empty();
    _results = [];
    for (i = _i = 0, _ref = items.length; 0 <= _ref ? _i < _ref : _i > _ref; i = 0 <= _ref ? ++_i : --_i) {
      _results.push(jQuery(list).append(items[i]));
    }
    return _results;
  };

}).call(this);