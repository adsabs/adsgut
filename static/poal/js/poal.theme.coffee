$ = jQuery

AjaxSolr.theme.prototype.result = (doc, snippet) ->
  output = '<div><h5>' + doc.title + '</h5>'
  user=$('#user').attr('user')
  bdict = 
    itemtype : 'ads/pub'
    uri : doc.bibcode
    name : doc.title
  console.log "USER", $('#user').attr('user')
  if $('#user').attr('user') is 'none'
    output += '<p id="links_' + doc.id + '" class="links">'+
      doc.bibcode+'</p>'
  else
    # output += '<p id="links_' + doc.id + '" class="links">'+
    #   doc.bibcode+'&nbsp;<button class="btn btn-mini saver" name="'+
    #   bdict.name+'" itemtype="'+bdict.itemtype+'" uri="'+bdict.uri+'">Save</button></p>'
    output += '<p id="links_' + doc.id + '" class="links">'+
      doc.bibcode+'</p>'+
      AjaxSolr.theme.prototype.saveform(doc, user)+
      AjaxSolr.theme.prototype.tagform(doc, user)+
      AjaxSolr.theme.prototype.groupform(doc, user)+
      AjaxSolr.theme.prototype.noteform(doc, user)

  output += '<p>' + snippet + '</p></div>'
  return output

#Each one of these will take doc, perhaps do a ajax request, and use output.
AjaxSolr.theme.prototype.saveform = (doc, user) ->
  output=''
  savedict = 
    itemtype : 'ads/pub'
    uri: doc.bibcode
    name: doc.bibcode
  formtext="""
  <div class="savediv">
    <form class="form-inline saveform">
        <button class="btn btn-mini saver" name="#{savedict.name}" itemtype="#{savedict.itemtype}" uri="#{savedict.uri}">Save</button>
    </form>
  </div>
  """
  output=output+formtext
  return output

AjaxSolr.theme.prototype.tagform = (doc, user) ->
  #get existing tags. Then create form for additional tagging.
  output=''
  tagdict = 
    itemtype : 'ads/pub'
    uri: doc.bibcode
    name: doc.bibcode
  formtext="""
  <div class="tagdiv">
    <i class="icon-play"></i>
    <form class="form-inline tagform" style="display:none">
        <input type="text" class="input-small tagtext" placeholder="tag"/>
        <button class="btn btn-mini tagadder" class="btn"><i class="icon-plus-sign"></i> Add Tag</button>
    </form>
    <span class="tagslist">no tags yet</span>
  </div>
  """
  output=output+formtext
  return output

AjaxSolr.theme.prototype.groupform = (doc, user) ->
  #get existing tags. Then create form for additional tagging.
  output=''
  groupdict = 
    itemtype : 'ads/pub'
    uri: doc.bibcode
    name: doc.bibcode
  formtext="""
  <div class="groupdiv">
    <i class="icon-play"></i>
    <form class="form-inline groupform" style="display:none">
        <label class="select">Group:
          <select multiple="multiple" class="groupselect">
          </select>
        </label>
        <label class="checkbox">
          <input type="checkbox" name="publicitem"> Make Public </input>
        </label>
        <button class="btn btn-mini tagadder" class="btn"><i class="icon-retweet"></i> Post</button>
    </form>
    <span class="groupslist">no groups yet</span>
  <div>
  """
  output=output+formtext
  return output

AjaxSolr.theme.prototype.noteform = (doc, user) ->
  #get existing tags. Then create form for additional tagging.
  output=''
  notedict = 
    itemtype : 'ads/pub'
    uri: doc.bibcode
    name: doc.bibcode
  formtext="""
  <div class="notediv">
    <i class="icon-chevron-right" state="right"></i>
    <form class="form-inline noteform"  style="display:none">
        <textarea class="notetext" placeholder="note"/>
        <label class="checkbox notelabel">
          <input type="checkbox" name="noteprivate"> Keep Note Private </input>
        </label>
        <button class="btn btn-mini noteadder" class="btn"><i class="icon-plus-sign"></i> Add Note</button>
    </form>
    <span class="noteslist">no notes yet</span>
  </div>
  """
  output=output+formtext
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

