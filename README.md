SETUP
=====
0. create a wiki user with 'bot' permissions
1. download pywikibot (https://pywikibot.toolforge.org/core_stable.zip)
2. extract the zipfile
3. place the following files in the pywikibot root directory:
- addons.py
- addons_category.py
- secretsfile
- user-config.py
4. place the following file in the pywikibot/families directory:
- xbmc_family.py
5. to speed things up, set seconds to 0 here:
- https://github.com/wikimedia/pywikibot/blob/46c9a900026092c6bb20c0092b4f76387dfdba38/pywikibot/throttle.py#L232


UPDATE WIKI PAGES
=================
0. open a terminal, navigate to the pywikibot root directory and run these commands:
1. python pwb.py login
2. python pwb.py addons.py
3. python pwb.py addons_category.py
