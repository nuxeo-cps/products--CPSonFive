# (C) Copyright 2010 Georges Racinet
# Author: Georges Racinet <georges@racinet.fr>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.

import os
import unittest
from Testing.ZopeTestCase import ZopeTestCase
from zope.app.testing.functional import ZCMLLayer

from zope.interface import Interface, implements
from OFS.SimpleItem import SimpleItem
from Products.CPSonFive.browser import AqSafeBrowserView

class IContent(Interface):
    pass

class Content(SimpleItem):
    implements(IContent)

    def __init__(self, zid):
        self._setId(zid)

config_file = os.path.join(os.path.dirname(__file__), 'cpsonfive.zcml')

CPSonFiveLayer = ZCMLLayer(config_file, __name__, 'CPSonFiveLayer')

class AqSafeTestView(AqSafeBrowserView):

    def meth(self):
        return 'ok'

class AqSafeBrowserViewTestCase(ZopeTestCase):
    layer = CPSonFiveLayer

    def afterSetUp(self):
        self.folder._setOb('content', Content('content'))
        self.view = self.folder.unrestrictedTraverse('content/aq_safe')

    def test_set_get(self):
        view = self.view
        view.aqSafeSet('content', view.context)
        content = view.aqSafeGet('content')
        # breaks with normal attribute set/get, see #2290
        expected = self.folder.absolute_url_path() + '/content'
        self.assertEquals(content.absolute_url_path(), expected)

    def test_get_missing(self):
        view = self.view
        self.assertRaises(AttributeError, view.aqSafeGet, 'nope')

    def test_set_del_get(self):
        view = self.view
        view.aqSafeSet('content', view.context)
        view.aqSafeDel('content')
        self.assertRaises(AttributeError, view.aqSafeGet, 'content')

    def test_default(self):
        d = 'not there'
        self.assertEquals(self.view.aqSafeGet('missing', d), d)

    def xtest_needed(self):
        # activate to know if the aqSafe stuff is useful (fails if not)
        view = self.view
        view.content = view.context
        self.assertRaises(Exception, view.content.absolute_url_path)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(AqSafeBrowserViewTestCase)))
