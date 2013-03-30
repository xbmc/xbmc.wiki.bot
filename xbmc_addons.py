# -*- coding: utf-8 -*-
"""
Reads addons.xml and creates/updates pages. 
Usage: xbmc_addons.py [repo]
where repo can be one of these:
 * Dharma
 * Eden
 * Frodo (default Repo)
 
"""
#
# Copyright (C) 2005-2013 Team XBMC
# http://www.xbmc.org
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
 
import wikipedia as pywikibot
import sys, urllib2, re
from BeautifulSoup import BeautifulStoneSoup # For processing XML
 
repoUrls={
    'Dharma':u'http://mirrors.xbmc.org/addons/dharma/',
    'Eden':u'http://mirrors.xbmc.org/addons/eden/',
    'Frodo':u'http://mirrors.xbmc.org/addons/frodo/',
    }
 
def UpdateAddons(*args):
	site = pywikibot.getSite()
	try:
		repoUrl = repoUrls[pywikibot.handleArgs(*args)[0]]
	except: 
		repoUrl = repoUrls['Frodo']
	pywikibot.output(u'Repo URL: ' + repoUrl)
	soup = importAddonXML(repoUrl + "addons.xml")
	for addon in soup.addons:
		newtext = None
		addontext = None
		oldtext = None
		iconUrl = None
		# Extract Add-on details from xml
		addon_data = extractAddonData(addon)	
		# Which Wiki page are we looking at?
		pagename = 'Add-on:' + addon_data['name']
		#pagename = 'Sandbox'	
 
		# Get content of wiki page
		page = pywikibot.Page(site, pagename)
		try:
			oldtext = page.get(force = False, get_redirect=True, throttle = True, sysop = False, change_edit_time = True)
		except pywikibot.NoPage:
			oldtext =  ''
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
			addontext = ("{{Addon \n|Name=" + addon_data['name'] + "\n|provider-name="+ addon_data['provider-name'] + 
			"\n|ID=" + addon_data['id'] + "\n|latest-version=" + addon_data['version']+ "\n|extension point=" + 
			addon_data['extension point'] + "\n|provides="+ addon_data['provides'] + "\n|Summary=" + 
			addon_data['summary'] + "\n|Description=" + addon_data['description'] +  "\n|Platform="+ 
			addon_data['platform'] + "\n|broken="+ addon_data['broken'] + "\n|icon url=" + iconUrl + "}}")
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
		# break
 
 
# Converts soup element into a tuple
# Gets english summaries/descriptions (if language specified)
# data: Soup addon element from repo addons.xml
def extractAddonData(data):
 
	addon = {'name' : data['name']}
	addon['id'] = data['id']
	addon['version'] = data['version']	
	try:
		addon['extension point'] = data.find('extension',library=True)['point']
	except:
		addon['extension point'] = data.extension['point']
 
	try:
		addon['provider-name'] = u""+data['provider-name'].replace('|',' & ')
	except:
		addon['provider-name'] = u""
 
	try:
		addon['provides'] = u""+data.find('extension',library=True).provides.string
	except:
		addon['provides'] = u""
 
	try:
		addon['summary'] = u""+data('summary', lang="en")[0].string
	except:
		try:
			addon['summary'] = u""+data.summary.string
		except:
			addon['summary'] = u""
 
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
		addon['broken'] = u""+data.broken.string
	except:
		addon['broken'] = u""
 
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
		addon['icon url'] = u''+addon['id']+'/icon.png'
 
	addon['summary'] = re.sub("\[CR\]","\\n",addon['summary'])	
	addon['description'] = re.sub("\[CR\]","\\n",addon['description'])
	return addon
 
# Download addons.xml and return Soup xml class
def importAddonXML(url):
	page = urllib2.urlopen(url)
	return BeautifulStoneSoup(page)
 
if __name__ == '__main__':
    try:
        UpdateAddons()
    finally:
        pywikibot.stopme()
