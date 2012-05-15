USERSET=set()
ITEMLIST=[]
ITEMSET=set()
ITEMTYPESET=set()
TAGLIST=[]
TAGSET=set()
TAGTYPESET=set()
GROUPSET=set()
APPSET=set()
PERMS=[]
ROUTES=[]
KVSTORE={}

#Configuration
USERSET.add('adsgut')
USERSET.add('ads')
GROUPSET.add('adsgut/default')
APPSET.add('ads/pubs')
ITEMTYPESET.add('ads/pub')
TAGTYPESET.add('ads/note')
TAGTYPESET.add('ads/comment')
APPSET.add('cds/objs')
ITEMTYPESET.add('cds/obj')
TAGTYPESET.add('cds/variability')

#USERSET
USERSET.add('rahuldave')
USERSET.add('jluker')
USERSET.add('romanchyla')
USERSET.add('giocalitri')

#GROUPSET
GROUPSET.add('rahuldave/ml')
GROUPSET.add('jluker/solr')

#How to add users to group, tags to items, items to group
#How to do visibility?
