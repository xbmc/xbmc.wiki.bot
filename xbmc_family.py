from pywikibot import family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'xbmc'
        self.langs = {
            'en': u'kodi.wiki',
        }

    def scriptpath(self, code):
        return {
            'en': u'',
        }[code]

    def version(self, code):
        return {
            'en': u'1.15.1',
        }[code]
