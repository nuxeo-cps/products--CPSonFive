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


from Products.Five.browser import BrowserView

_missing_value = object()

class AqSafeBrowserView(BrowserView, object):
    """Base class protecting against some acquisition insanity (see #2290)
    """

    def __init__(self, *a, **k):
        self._aq_safe = {}
        return BrowserView.__init__(self, *a, **k)

    def aqSafeGet(self, k, default=_missing_value):
        if default is _missing_value:
            try:
                return self._aq_safe[k]
            except KeyError:
                raise AttributeError(k)

        return self._aq_safe.get(k, default)

    def aqSafeSet(self, k, v):
        self._aq_safe[k] = v

    def aqSafeDel(self, k):
        try:
            del self._aq_safe[k]
        except KeyError:
            raise AttributeError(k)

