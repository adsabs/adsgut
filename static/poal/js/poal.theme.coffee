$ = jQuery

AjaxSolr.theme.prototype.result = (doc, snippet) ->
  output = '<div><h5>' + doc.title + '</h5>'
  bdict = 
    itemtype : 'ads/pub'
    uri : doc.bibcode
    name : doc.title
  console.log "USER", $('#user').attr('user')
  if $('#user').attr('user') is 'none'
    output += '<p id="links_' + doc.id + '" class="links">'+
      doc.bibcode+'</p>'
  else
    output += '<p id="links_' + doc.id + '" class="links">'+
      doc.bibcode+'&nbsp;<button class="btn btn-mini saver" name="'+
      bdict.name+'" itemtype="'+bdict.itemtype+'" uri="'+bdict.uri+'">Save</button></p>'
  output += '<p>' + snippet + '</p></div>'
  return output


AjaxSolr.theme.prototype.snippet = (doc) -> 
  output = ''
  output += '<span style="display:none;">' + JSON.stringify(doc)
  output += '</span> <a href="#" class="more">more</a>'
  return output


AjaxSolr.theme.prototype.tag = (value, num, weight, handler) -> 
  return $('<a href="#" class="tagcloud_item"/>').text(value+ '('+num+')').addClass('tagcloud_size_' + weight).click(handler)

AjaxSolr.theme.prototype.simpletag = (value, handler) -> 
  return $('<a href="#"/>').text(value).click(handler)


AjaxSolr.theme.prototype.facet_link = (value, handler) ->
  return $('<a href="#"/>').text(value).click(handler)


AjaxSolr.theme.prototype.facet_link_header = (header, value, handler) ->
  return $('<span class="bold"/>').text(header+": ").append($('<a href="#"/>').text(value).click(handler))


AjaxSolr.theme.prototype.no_items_found = () ->
  return 'no items found in current selection'

AjaxSolr.theme.prototype.list_concat = (list, items, separator) -> 
  jQuery(list).empty()
  for i in [0...items.length]   
    jQuery(list).append(items[i])

