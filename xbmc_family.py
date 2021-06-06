from pywikibot import family

class Family(family.Family):
    name = 'xbmc' # Set the family name; this should be the same as in the filename.
    langs = {'en': u'kodi.wiki'} # Put the hostname here.

    def scriptpath(self, code):
        return {'en': u''}[code] # The relative path of index.php, api.php : look at your wiki address.

    def version(self, code):
        return {'en': u'1.36.0'}[code] # Not very important in most cases. Needed for older versions

    def protocol(self, code):
        """Return the protocol for this family."""
        return 'https' # to support HTTPS
