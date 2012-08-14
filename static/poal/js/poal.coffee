$=jQuery

$ ->
  Manager = new AjaxSolr.Manager(solrUrl: 'http://localhost:8983/solr/')


  fields= [ 'author_facet', 'keyword_facet']
  numeric_fields = []
  autocomplete_fields = ['author_facet', 'keyword_facet']
  min_numericfields=[]
  max_numericfields=[]
  step_numericfields=[]
  Manager.addWidget(new AjaxSolr.ResultWidget(
      id: 'result',
      target: '#docs'
  ))
  Manager.addWidget(new AjaxSolr.PagerWidget(
      id: 'pager',
      target: '#pager',
      separator: '',
      prevLabel: '&lt;',
      nextLabel: '&gt;',
      innerWindow: 1,
      renderHeader: (perPage, offset, total) -> 
        $('#pager-header').html($('<span/>').text('displaying ' + Math.min(total, offset + 1) + ' to ' + Math.min(total, offset + perPage) + ' of ' + total))
  ))

  Manager.addWidget(new AjaxSolr.CurrentSearchWidget(id: 'currentsearch', target: '#selection'))

  # for i in [0...numeric_fields.length]
  #     Manager.addWidget(new AjaxSolr.HfDualSliderWidget(
  #       id: numeric_fields[i],
  #       target: '#' + numeric_fields[i],
  #       field: numeric_fields[i],
  #       datamin: min_numericfields[i],
  #       datamax: max_numericfields[i],
  #       datastep: step_numericfields[i]
  #     ))
  for i in [0...fields.length]
      Manager.addWidget(new AjaxSolr.TagcloudWidget(
        id: fields[i],
        target: '#' + fields[i],
        field: fields[i]
      ))
  Manager.addWidget(new AjaxSolr.AutocompleteWidget(
    id: 'text',
    target: '#search',
    field: 'text',
    fields: autocomplete_fields
  ))
  Manager.setStore(new AjaxSolr.ExtHashStore())
  Manager.store.exposed = [ 'fq', 'q' ]

  Manager.init();
  Manager.store.addByValue('q', '*:*')
  #'facet.field': all_fields,
  params = 
    facet: true,
    'facet.field': _.union(fields,numeric_fields),
    'facet.limit': 20,
    'rows': 0,
    'facet.mincount': 1,
    'json.nl': 'map',
    'stats': 'true',
    'stats.field': numeric_fields

  for name of params
    Manager.store.addByValue(name, params[name])


  #Set up event handlers
  console.log "Setting up Event handlers"
  dauser=$('#user').attr('user')
  $('#docs').delegate "button.saver", "click", () ->
    bdict = 
      'itemtype': $(this).attr('itemtype')
      'uri': $(this).attr('uri')
      'name': $(this).attr('name')
    console.log dauser, bdict
    $.post "/user/"+dauser+"/item", bdict, (data) =>
      console.log('data is', data);
      if (data['status'] is 'OK')
          $(this).hide()           
    return false
  Manager.doRequest()


$.fn.showIf = (condition) ->
  if condition
    return this.show()
  else 
    return this.hide()


