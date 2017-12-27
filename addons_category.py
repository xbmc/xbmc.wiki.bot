# -*- coding: utf-8 -*-
"""
Reads addons.xml and creates/updates category pages.
Usage: python pwb.py addons_category.py
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


import sys, urllib2, re, zlib
from BeautifulSoup import BeautifulStoneSoup # For processing XML
from pywikibot.compat import catlib
from pywikibot import pagegenerators
import pywikibot

repoUrls={
    'Gotham':u'http://mirrors.kodi.tv/addons/gotham/',
    'Helix':u'http://mirrors.kodi.tv/addons/helix/',
    'Isengard':u'http://mirrors.kodi.tv/addons/isengard/',
    'Jarvis':u'http://mirrors.kodi.tv/addons/jarvis/',
    'Krypton':u'http://mirrors.kodi.tv/addons/krypton/',
    'Leia':u'http://mirrors.kodi.tv/addons/leia/',
    }

repoCats={
    'Gotham':u'Gotham add-on repository',
    'Helix':u'Helix add-on repository',
    'Isengard':u'Isengard add-on repository',
    'Jarvis':u'Jarvis add-on repository',
    'Krypton':u'Krypton add-on repository',
    'Leia':u'Leia add-on repository',
    }

def UpdateRepoCats(*args):
    # Get List of all articles in Category:All add-ons
    site = pywikibot.getSite()

    # Download all repos as soup element
    soups = importAllAddonXML()

    # Get all pages in Category All add-ons
    cat = catlib.Category(site, u'Category:All add-ons')
    pages = cat.articlesList(False)
    allRepoCats = repoCatList(site)
    
    for Page in pagegenerators.PreloadingGenerator(pages,100):
        # Get addon_id via regexp
        addon_id = None
        addon_id = re.search("\|ID=([a-zA-Z0-9_\.\-]+)",Page.get())
        if not addon_id:
            pywikibot.output("Can't find addon_id for %s, skipping it..." % Page.title())
            continue
        else:
            addon_id = addon_id.group(1)
            pywikibot.output("Identifying Repos for %s." % addon_id)
        # See if addon_id can be found in repos
        repos = checkInRepo(addon_id, soups)
        addRemoveRepoCats(Page, repos, allRepoCats)

def repoCatList(site):
    CatList = []
    for repoName, repoCat in repoCats.iteritems():
        CatList.append(catlib.Category(site, 'Category:'+ repoCat))
    return CatList

def addRemoveRepoCats(article, repos, allRepoCats, comment=None):
    # Create list of repos to be removed
    notRepos = []

    if not article.canBeEdited():
        pywikibot.output("Can't edit %s, skipping it..." % article.aslink())
        return False

    cats = article.categories(get_redirect=True)
    site = article.site
    changesMade = False
    newCatList = []
    newCatSet = set()

    repoCatList = []

    #remove all repos
    for cat in cats:
        if cat in allRepoCats:
            changesMade = True
            continue
        if cat.title() not in newCatSet:
            newCatSet.add(cat.title())
            newCatList.append(cat)

    #add relevant repos
    for i in range(len(repos)):
        repo = repos[i]
        newCatList.append(catlib.Category(site, 'Category:'+ repoCats[repo]))
        changesMade = True

    if not changesMade:
        pywikibot.output(u'No changes necessary to %s!' % article.title())
    else:
        text = article.get(get_redirect=True)
        try:
            text = pywikibot.replaceCategoryLinks(text, newCatList)
        except ValueError:
            # Make sure that the only way replaceCategoryLinks() can return
            # a ValueError is in the case of interwiki links to self.
            pywikibot.output(
                u'Skipping %s because of interwiki link to self' % article)
        try:
            article.put(text, comment='Addon-Bot repo category update', watchArticle = None, minorEdit = True)
        except pywikibot.EditConflict:
            pywikibot.output(
                u'Skipping %s because of edit conflict' % article.title())
        except pywikibot.SpamfilterError, e:
            pywikibot.output(
                u'Skipping %s because of blacklist entry %s'
                % (article.title(), e.url))
        except pywikibot.LockedPage:
            pywikibot.output(
                u'Skipping %s because page is locked' % article.title())
        except pywikibot.PageNotSaved, error:
            pywikibot.output(u"Saving page %s failed: %s"
                         % (article.aslink(), error.message))

def checkInRepo(addon_id, soups):
    repos = [ ]
    for repoName, soup in soups.iteritems():
        if soup.find('addon',id=addon_id):
            repos.append(repoName)
    return repos

def importAllAddonXML():
    soup = { }
    for repoName, repoUrl in repoUrls.iteritems():
        try:
            soup[repoName] = importAddonXML(repoUrl + "addons.xml.gz")
        except urllib2.HTTPError:
            soup[repoName] = importAddonXML(repoUrl + "addons.xml")
    return soup
    
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
        UpdateRepoCats()
    finally:
        pywikibot.stopme()
