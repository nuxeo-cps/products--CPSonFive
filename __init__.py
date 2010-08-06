# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
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
#
# $Id: zopecal.py 24305 2005-06-22 14:39:11Z lregebro $

""" CPSonFive

This product is the container for any reusable integration between CPS and Five.
"""
from zope.interface import implements

from types import StringTypes
from zope.schema.interfaces import ITitledTokenizedTerm
from zope.i18nmessageid import Message

# Zope3.0.0 doesn't translates dropdownboxes (that's a bug)
def textForValue(self, term):
    """Extract a string from the term.

    The term must be a vocabulary tokenized term.

    This can be overridden to support more complex term objects. The token
    is returned here since it's the only thing known to be a string, or
    str()able."""
    if ITitledTokenizedTerm.providedBy(term):
        return self.translate(term.title)
    return self.translate(term.token)


from zope.i18n.interfaces import IUserPreferredCharsets
from ZPublisher import Converters

class ZPublisherCharset(object):
    # This object implements the selector function for IUserPreferredCharsets
    # but doesn't care what the user prefer, It returns what's specified in
    # zope.conf
    implements(IUserPreferredCharsets)

    def __init__(self, request):
        self.request = request

    def getPreferredCharsets(self):
        '''See interface IUserPreferredCharsets'''
        return [Converters.default_encoding]

from zope.event import notify
from Products.Five.form import EditView, Update, applyWidgetsChanges
from zope.app.form.interfaces import WidgetsError
from zope.app.form.utility import setUpEditWidgets, applyWidgetsChanges
from zope.app.event.objectevent import ObjectModifiedEvent
try:
    from zope.app.i18n import ZopeMessageFactory as _
except:
    from zope.app.i18n import ZopeMessageIDFactory as _
import transaction, datetime

def EditViewUpdate(self):
    if self.update_status is not None:
        # We've been called before. Just return the status we previously
        # computed.
        return self.update_status

    status = ''

    content = self.adapted

    if Update in self.request.form.keys():
        changed = False
        try:
            changed = applyWidgetsChanges(self, self.schema,
                target=content, names=self.fieldNames)
            # We should not generate events when an adapter is used.
            # That's the adapter's job.  We need to unwrap the objects to
            # compare them, as they are wrapped differently.
            # Additionally, we can't use Acquisition.aq_base() because
            # it strangely returns different objects for these two even
            # when they are identical.  In particular
            # aq_base(self.adapted) != self.adapted.aq_base :-(
            if changed and getattr(self.context, 'aq_base', self.context)\
                        is getattr(self.adapted, 'aq_base', self.adapted):
                notify(ObjectModifiedEvent(content))
        except WidgetsError, errors:
            self.errors = errors
            status = _("An error occurred.")
            transaction.abort()
        else:
            setUpEditWidgets(self, self.schema, source=self.adapted,
                             ignoreStickyValues=True,
                             names=self.fieldNames)
            if changed:
                self.changed()
                # CPS Patch begins here.
                localizer = getattr(self.context, 'Localizer', None)
                if localizer is not None:                    
                    status = localizer.default("Updated on %(date_time)s")
                    format = str(localizer.default('date_medium'))
                    date = datetime.datetime.now().strftime(format)
                else:
                    date = str(datetime.utcnow())
                    
                status = _("Updated on ${date_time}",
                           mapping={'date_time': date})

    self.update_status = status

    return status

from zope.i18n.interfaces import IUserPreferredLanguages, ILanguageAvailability

class UserLanguages(object):
    """Return the preferred language.
    
    This one cares about the LOCALIZER_LANGUAGE used by CPS/Localizer to
    explicitly select a language. The LocalizerLanguages component in Five
    also does this, but via the overcomplicated Localizer.AcceptLanguage 
    who seldom returns what we want or expect.
    So I use this instead. //Lennart."""
    implements(IUserPreferredLanguages)

    def __init__(self, request):
        self.request = request

    def getPreferredLanguages(self):
        accept_language = self.request.HTTP_ACCEPT_LANGUAGE
        localizer_language = self.request.get('LOCALIZER_LANGUAGE')
        accept_language = '%s;q=2.0,%s' % (localizer_language, accept_language)
        # Normalize: Remove any spaces, change _ to -, make all lowercase:
        accept_language = accept_language.replace(' ', '')
        accept_language = accept_language.replace('_', '-')
        accept_language = accept_language.lower()
        langs = {}
        for lang in accept_language.split(','):
            if lang.find(';') != -1:
                lang, q = lang.split(';')
                q = float(q[2:]) # remove the "q=" and make into a float
            else:
                q = 1.0
            if lang not in langs:
                langs[lang] = q
                    
        # Make into a list of tuples with value first, and key last 
        # for easy sorting:
        langs = [(q,l) for (l,q) in langs.items()]
        langs.sort()
        langs.reverse()
        # Return languages in order of quality
        return [l for q, l in langs]

class CPSLanguages(object):
    """Returns the languages that exist in a CPS site"""
    
    implements(ILanguageAvailability)

    def __init__(self, context):
        self.context = context
        
    def getAvailableLanguages(self):
        pts = self.context.translation_service
        languages = []
        for lang in [pts.getDefaultLanguage()] + pts.getSupportedLanguages():
            # Localizer uses the format xx_YY instead of xx-yy:
            lang = lang.replace('_', '-')
            lang = lang.lower()
            if lang not in languages:
                languages.append(lang)
        return languages        
    
def initialize(context):

    # Zope3monkey
    from zope.app.form.browser.itemswidgets import ItemsWidgetBase
    ItemsWidgetBase.textForValue = textForValue
    # Five monkey
    EditView.update = EditViewUpdate
