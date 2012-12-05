from errors import abort, doabort

AUTHTOKENS={
	'SAVE_ITEM_FOR_USER': (1001, "App or Group can save item for user"),
	'POST_ITEM_FOR_USER': (1002, "App or Group can post item for user into app or group"),
	'TAG_ITEM_FOR_USER':  (1003, "App or Group can tag item for user"),
	'POST_TAG_FOR_USER':  (1004, "App or Group can post tag for user on an item to app or group")
}
def permit(clause, reason):
	if clause==False:
		doabort('NOT_AUT', {'reason':reason})

def permit2(authstart, clausetuples):
	start=authstart
	reasons=[]
	for tup in clausetuples:
		start = start or tup[0]
		reasons.append(tup[1])
	if start==False:
		doabort('NOT_AUT', {'reason':' or '.join(reasons)})


#add permission helpers here to refactor permits
#example group membership etc

#(1) user must be defined

#perhaps we'll need multiple authorizers.
#Where do we check for oauth? not here. That must come in via authstart,
#somehow knocked into g.db and then computed upon.
#authorize with useras=currentuser will allow u through if u r either 
#logged in or are superuser. useras=None will only allow you if u r systemuser
def authorize(authstart, db, currentuser, useras):
	permit(currentuser!=None, "must be logged in")
	clause = (currentuser==useras, "User %s not authorized" % currentuser.nick)
	clausesys = (db.isSystemUser(currentuser), "User %s not superuser" % currentuser.nick)
	permit2(authstart, [clausesys, clause])


#For next two, for additions and such, switch between useras=currentuser and useras=None
#where a useras is not required
def authorize_context_owner(authstart, db, currentuser, useras, cobj):
	permit(currentuser!=None, "must be logged in")
	clause = (currentuser==useras, "User %s not authorized" % currentuser.nick)
	clausesys = (db.isSystemUser(currentuser), "User %s not superuser" % currentuser.nick)
	if cobj.__class__.__name__=='Group':
		clause3=(db.isOwnerOfGroup(currentuser,cobj), "must be owner of group %s" % cobj.fqin)
	elif cobj.__class__.__name__=='Application':
		clause3=(db.isOwnerOfApp(currentuser,cobj), "must be owner of app %s" % cobj.fqin)
	permit2(authstart, [clausesys, clause3, clause])

def authorize_context_member(authstart, db, currentuser, useras, cobj):
	permit(currentuser!=None, "must be logged in")
	clause = (currentuser==useras, "User %s not authorized" % currentuser.nick)
	clausesys = (db.isSystemUser(currentuser), "User %s not superuser" % currentuser.nick)
	if cobj.__class__.__name__=='Group':
		clause3=(db.isMemberOfGroup(currentuser,cobj), "must be member of group %s" % cobj.fqin)
	elif cobj.__class__.__name__=='Application':
		clause3=(db.isMemberOfApp(currentuser,cobj), "must be member of app %s" % cobj.fqin)
	permit2(authstart, [clausesys, clause3, clause])


