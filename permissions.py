from errors import abort

def permit(clause, reason):
	if clause==False:
		abort(401, {'reason':reason})


#add permission helpers here to refactor permits
#example group membership etc

#(1) user must be defined