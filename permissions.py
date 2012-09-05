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

#add permission helpers here to refactor permits
#example group membership etc

#(1) user must be defined