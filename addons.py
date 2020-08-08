# -*- coding: utf-8 -*-
"""
Reads addons.xml and creates/updates addon pages.
Usage: python pwb.py addons.py [repo]
where repo (optional) can be one of these:
 * Gotham
 * Helix
 * Isengard
 * Jarvis
 * Krypton
 * Leia (default)
"""
#
# Copyright (C) 2005-2015 Team Kodi
# http://kodi.tv
#
# This Program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This Program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with XBMC; see the file COPYING. If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# http://www.gnu.org/copyleft/gpl.html

import pywikibot
import sys, urllib2, re, zlib, os
from BeautifulSoup import BeautifulStoneSoup # For processing XML

repoUrls={'Gotham':u'http://mirrors.kodi.tv/addons/gotham/',
          'Helix':u'http://mirrors.kodi.tv/addons/helix/',
          'Isengard':u'http://mirrors.kodi.tv/addons/isengard/',
          'Jarvis':u'http://mirrors.kodi.tv/addons/jarvis/',
          'Krypton':u'http://mirrors.kodi.tv/addons/krypton/',
          'Leia':u'http://mirrors.kodi.tv/addons/leia/',
          'Matrix':u'http://mirrors.kodi.tv/addons/matrix/',
         }

def UpdateAddons(*args):
    site = pywikibot.getSite()
    try:
        repoUrl = repoUrls[pywikibot.handleArgs(*args)[0]]
    except:
        repoUrl = repoUrls['Leia']
    pywikibot.output(u'Repo URL: ' + repoUrl)
    try:
      soup = importAddonXML(repoUrl + 'addons.xml.gz')
    except urllib2.HTTPError:
      soup = importAddonXML(repoUrl + 'addons.xml')
    processed = []
    for addon in soup.addons:
        newtext = None
        addontext = None
        oldtext = None
        iconUrl = None
        # Extract Add-on details from xml
        addon_data = extractAddonData(addon)
        # Binary addons have multiple (platform specific) copies in the repo, process only 1 of them
        if addon_data['id'] in processed:
            continue
        processed.append(addon_data['id'])
        # Which Wiki page are we looking at?
        pagename = 'Add-on:' + addon_data['name']
        #pagename = 'Sandbox'

        # Get content of wiki page
        page = pywikibot.Page(site, pagename)
        try:
            oldtext = page.get(force = False, get_redirect = True, throttle = True, sysop = False, change_edit_time = True)
        except pywikibot.NoPage:
            oldtext =  ''
            pywikibot.output(u'%s not found' % pagename)
        except pywikibot.IsRedirectPage:
            pywikibot.output(u'%s is a redirect!' % pagename)
        except pywikibot.Error: # third exception, take the problem and print
            pywikibot.output(u"Some Error, skipping..")
            continue

        if addon_data['icon url'] != u"":
            iconUrl = repoUrl + addon_data['icon url']
        else:
            iconUrl = u""
        # Create Addon template
        try:
            addontext = ("{{Addon \n|Name=" + addon_data['name'] +
                         "\n|provider-name="+ addon_data['provider-name'] +
                         "\n|ID=" + addon_data['id'] +
                         "\n|latest-version=" + addon_data['version']+
                         "\n|extension point=" + addon_data['extension point'] +
                         "\n|provides="+ addon_data['provides'] +
                         "\n|Summary=" + addon_data['summary'] +
                         "\n|Description=" + addon_data['description'] +
                         "\n|Platform=" + addon_data['platform'] +
                         "\n|Language=" + addon_data['language'] +
                         "\n|License=" + addon_data['license'] +
                         "\n|Forum=" + addon_data['forum'] +
                         "\n|Website=" + addon_data['website'] +
                         "\n|Source=" + addon_data['source'] +
                         "\n|Email=" + addon_data['email'] +
                         "\n|broken=" + addon_data['broken'] +
                         "\n|icon url=" + iconUrl + "}}")
        except:
            pywikibot.output(u"Some Error creating Addons String, skipping..")
            continue

        # Replace existing Addon template
        templateRegex = re.compile(r'\{\{ *(' + ':|'+ \
                                   r':|[mM][sS][gG]:)?Addon' + \
                                   r'(?P<parameters>\s*\|.+?|) *}}',
                                   re.DOTALL)
        replacedText = re.subn(templateRegex, addontext, oldtext)

        if replacedText[1] > 0:
            newtext = replacedText[0]
        else:
            newtext = addontext + "\n" + oldtext
        # print newtext (debug)
        # pywikibot.output(newtext)

        # Push new page to wiki
        try:
            page.put(newtext, comment='Addon-Bot Update', watchArticle = None, minorEdit = True)
        except pywikibot.LockedPage:
            pywikibot.output(u"Page %s is locked; skipping." % page.aslink())
        except pywikibot.EditConflict:
            pywikibot.output(u'Skipping %s because of edit conflict' % (page.title()))
        except pywikibot.SpamfilterError, error:
            pywikibot.output(u'Cannot change %s because of spam blacklist entry %s' % (page.title(), error.url))
        except:
            pywikibot.output(u"Some Error writing to wiki page, skipping..")
            continue
        # break here for testing purposes
#        break


# Converts soup element into a tuple
# Gets english summaries/descriptions (if language specified)
# data: Soup addon element from repo addons.xml
def extractAddonData(data):

    addon = {'name' : data['name']}
    addon['id'] = data['id']
    addon['version'] = data['version']
    try:
        addon['extension point'] = data.extension['point']
    except:
        addon['extension point'] = ""

    try:
        addon['provider-name'] = u""+data['provider-name'].replace('|',' & ')
    except:
        addon['provider-name'] = u""

    if addon['extension point'] == 'xbmc.python.pluginsource' or addon['extension point'] == 'xbmc.python.script':
        try:
            addon['provides'] = u""+data.find('extension',library=True).provides.string
        except:
            addon['provides'] = u""
    else:
        addon['provides'] = u""

    try:
        addon['summary'] = u""+data('summary', lang="en_GB")[0].string
    except:
        try:
            addon['summary'] = u""+data('summary', lang="en")[0].string
        except:
            try:
                addon['summary'] = u""+data.summary.string
            except:
                addon['summary'] = u""

    try:
        addon['description'] = u""+data('description', lang="en_GB")[0].string
    except:
        try:
            addon['description'] = u""+data('description', lang="en")[0].string
        except:
            try:
                addon['description'] = u""+data.description.string
            except:
                addon['description'] = u""

    try:
        addon['platform'] = u""+data.platform.string
    except:
        addon['platform'] = u""

    try:
        addon['language'] = u""+data.language.string
    except:
        addon['language'] = u""
        
    try:
        addon['license'] = u""+data.license.string
    except:
        addon['license'] = u""

    try:
        addon['forum'] = u""+data.forum.string
    except:
        addon['forum'] = u""

    try:
        addon['website'] = u""+data.website.string
    except:
        addon['website'] = u""

    try:
        addon['source'] = u""+data.source.string
    except:
        addon['source'] = u""

    try:
        addon['email'] = u""+data.email.string
    except:
        addon['email'] = u""

    try:
        addon['broken'] = u""+data.broken.string
    except:
        addon['broken'] = u""

    try:
        addon['path'] = u""+os.path.split(data.path.string)[0]
    except:
        addon['path'] = u""

    try:
        if data.noicon.string == u"true":
            addon['noicon'] = True
        else:
            addon['noicon'] = False
    except:
        addon['noicon'] = False

    if addon['noicon']:
        addon['icon url'] = u""
    else:
        try:
            addon['icon url'] = u""+addon['path']+'/'+data.assets.icon.string
        except:
            addon['icon url'] = u''+addon['path']+'/icon.png'

    addon['summary'] = re.sub("\[CR\]","\\n",addon['summary'])
    addon['description'] = re.sub("\[CR\]","\\n",addon['description'])
    return addon

# Download addons.xml and return Soup xml class
def importAddonXML(url):
    headers = {'User-Agent':'Kodi-AddonBot'}
    req = urllib2.Request(url, None, headers)
    page = urllib2.urlopen(req)
    if page.headers.get('Content-Type').find('gzip') >= 0 or page.headers.get('Content-Type').find('application/octet-stream') >= 0:
      d = zlib.decompressobj(16+zlib.MAX_WBITS)
      page = d.decompress(page.read())
    return BeautifulStoneSoup(page)

if __name__ == '__main__':
    try:
       UpdateAddons()
    finally:
       pywikibot.stopme()
