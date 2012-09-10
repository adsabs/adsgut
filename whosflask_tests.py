import os
import whosflask
import unittest
import tempfile



class FlaskrTestCase(unittest.TestCase):

	def setUp(self):
		whosflask.adsgut.config['TESTING'] = True
		self.app = whosflask.adsgut.test_client()


	def tearDown(self):
		pass

	def login(self, username):
	    return self.app.post('/login', data=dict(
	        username=username,
	        logged_in=True
	    ), follow_redirects=True)

	def logout(self):
		return self.app.get('/logout', follow_redirects=True)

	def getHelper(self, prefix, url, assertion=None):
		print '----------------------------------------'
		print 'TEST:', prefix+url
		print '----------------------------------------'
		return self.app.get(prefix+url).data

	def test_user_endpoints(self):
		nick='rahuldave'
		prefix="/user/%s" % nick
		self.login(nick)
		# @adsgut.route'/user/<nick>'
		# @adsgut.route'/user/<nick>/appsin'
		# @adsgut.route'/user/<nick>/appsinvited'
		# @adsgut.route'/user/<nick>/appsowned'
		# @adsgut.route'/user/<nick>/groupsin'
		# @adsgut.route'/user/<nick>/groupsinvited'
		# @adsgut.route'/user/<nick>/groupsowned'
		print self.getHelper(prefix, '')

		print self.getHelper(prefix, '/appsin')
		print self.getHelper(prefix, '/appsinvited')
		print self.getHelper(prefix, '/appsowned')

		print self.getHelper(prefix, '/groupsin')
		print self.getHelper(prefix, '/groupsinvited')
		print self.getHelper(prefix, '/groupsowned')
		assert 1

	def test_user_item_endpoints(self):
		nick='rahuldave'
		prefix="/user/%s" % nick
		self.login(nick)
		# @adsgut.route'/user/<nick>/items'  |   q=fieldlist=['itemtype','', 'context', None, 'fqin', None]
		print self.getHelper(prefix, '/items')
		print self.getHelper(prefix, '/items?itemtype=ads/pub')
		print self.getHelper(prefix, '/items?itemtype=ads/pub&context=group&fqin=rahuldave/group:ml')
		print self.getHelper(prefix, '/items?context=app&fqin=ads/app:publications')

	def test_user_tag_endpoints(self):
		nick='rahuldave'
		prefix="/user/%s" % nick
		self.login(nick)
		# @adsgut.route'/user/<nick>/tags'  |   q=fieldlist=['tagname','', 'tagtype','', 'context', None, 'fqin', None]
		print self.getHelper(prefix, '/tags')
		print self.getHelper(prefix, '/tags?itemtype=ads/pub')
		print self.getHelper(prefix, '/tags?tagtype=ads/tag&context=group&fqin=rahuldave/group:ml')
		print self.getHelper(prefix, '/tags?context=app&fqin=ads/app:publications')

	def test_app_get_endpoints(self):
		print "************"
		nick='ads'
		prefix="/app/%s" % nick
		self.login(nick)
		# @adsgut.route'/app', methods=['POST']  |   name/description
		# @adsgut.route'/app/<appowner>/app:<appname>/acceptinvitation', methods=['POST']  |   accept
		# @adsgut.route'/app/<appowner>/app:<appname>/groups', methods=['GET', 'POST']  |   group
		# @adsgut.route'/app/<appowner>/app:<appname>/invitation', methods=['POST']  |   user
		# @adsgut.route'/app/<appowner>/app:<appname>/items', methods=['POST']  |   user/fqin
		# @adsgut.route'/app/<appowner>/app:<appname>/itemsandtags', methods=['POST']  |   user/name/itemtype/description/uri/tags=[[name, tagtype, description]...]
		# @adsgut.route'/app/<appowner>/app:<appname>/tags', methods=['POST']  |   user/fqin/fqtn
		# @adsgut.route'/app/<appowner>/app:<appname>/users', methods=['GET', 'POST']  |   user
		# @adsgut.route'/app/<username>/app:<appname>'
		print self.getHelper(prefix, '/app:publications')
		print self.getHelper(prefix, '/app:publications/groups')
		print self.getHelper(prefix, '/app:publications/users')

	def test_group_get_endpoints(self):
		print "************"
		nick='rahuldave'
		prefix="/group/%s" % nick
		self.login(nick)
		# @adsgut.route'/group', methods=['POST']  |   groupname/description
		# @adsgut.route'/group/<groupowner>/group:<groupname>/acceptinvitation', methods=['POST']  |   accepr
		# @adsgut.route'/group/<groupowner>/group:<groupname>/invitation', methods=['POST']  |   user
		# @adsgut.route'/group/<groupowner>/group:<groupname>/items', methods=['POST']  |   user/fqin
		# @adsgut.route'/group/<groupowner>/group:<groupname>/itemsandtags', methods=['POST']  |   user/name/itemtype/description/uri/tags=[[name, tagtype, description]...]
		# @adsgut.route'/group/<groupowner>/group:<groupname>/tags', methods=['POST']  |   user/fqin/fqtn
		# @adsgut.route'/group/<groupowner>/group:<groupname>/users', methods=['GET', 'POST']  |   user
		# @adsgut.route'/group/<username>/group:<groupname>'
		print self.getHelper(prefix, '/group:ml')
		print self.getHelper(prefix, '/group:ml/users')

	def test_singular_item_endpoint(self):
		pass

	def test_singular_tag_endpoint(self):
		pass

	def test_items_nick_endpoint(self):
		nick='rahuldave'
		prefix="/items/%s" % nick
		self.login(nick)
		tagger='/ads/tag:stupid'
		# @adsgut.route'/items/<nick>/<tagspace>/<tagtypename>:<tagname>'  |   q=fieldlist=['uri','', 'name','', 'itemtype','', 'context', None, 'fqin', None]
		# @adsgut.route'/items/<nick>/byspec'  |   q=fieldlist=['tagname','', 'tagtype','', 'context', None, 'fqin', None, 'itemuri', '', 'itemname', '', 'itemtype', '']
		print self.getHelper(prefix, tagger)
		print self.getHelper(prefix, tagger+'?itemtype=ads/pub2')
		print self.getHelper(prefix, '/byspec?itemname=hello%20kitty')

	def test_tags_nick_endpoint(self):
		pass

	def test_items_endpoint(self):
		# @adsgut.route'/items/<nick>', methods=['POST']  |   name/itemtype/uri/description
		pass

	def test_tags_endpoint(self):
		pass


if __name__ == '__main__':
	unittest.main()