# -*- coding: utf-8 -*

from __future__ import absolute_import, unicode_literals
import pywikibot
from pywikibot import pagegenerators
import json, sys, os
import requests

if sys.version_info[0] < 3:
    print ('Não podemos executar o bot em versões inferiores a 3')
    os._exit(0)

from urllib import request

def scores(revs):
    url = 'https://ores.wmflabs.org/v3/scores/ptwiki/?models=goodfaith|damaging&revids='+('|').join(revs)
    retornar = {}
    r = requests.get(url=url)
    data = r.json()
    for rev in revs:
        goodfaith = data.get('ptwiki').get('scores').get(rev).get('goodfaith')
        damaging = data.get('ptwiki').get('scores').get(rev).get('damaging')
        previsao = goodfaith.get('score').get('prediction')
        probabilidade = goodfaith.get('score').get('probability').get('true')
        d_previsao = damaging.get('score').get('prediction')
        d_probabilidade = damaging.get('score').get('probability').get('true')
        retornar[rev] = {'boa_fe': previsao, 'prob': probabilidade, 'danosa': d_previsao, 'prob_d': d_probabilidade}
    return retornar

def score(rev):
    return scores([rev]).get(rev)

Site = pywikibot.Site()

if Site.logged_in() == False:
    Site.login()

for page in pagegenerators.LiveRCPageGenerator(site=Site):
    if page._rcinfo.get('type') == 'edit' and page._rcinfo.get('namespace') in [0, 100] and page._rcinfo.get('user') != Site.username():
        revision = page._rcinfo.get('revision')
        ores = score(str(revision.get('new')))
        print ('>' if ores.get('prob') < 0.095 else ' ', revision.get('new'), ores.get('prob'), ores.get('prob_d'), page.title(), page._rcinfo.get('user'))
        if ores.get('prob') < 0.095 or ores.get('prob_d') > 0.97 or (ores.get('prob') < 0.13 and ores.get('prob_d') > 0.95):
            old = page.text
            page.text = page.getOldVersion(revision.get('old'))
            pywikibot.showDiff(old, page.text)
            try:
                #page.save(u'BOT - Reversão de página ([[:mw:ORES|ORES]]: '+ str(ores.get('prob'))+')')

                token = pywikibot.data.api.Request(site=Site, parameters={'action': 'query', 'meta':'tokens', 'type': 'rollback'}).submit()['query']['tokens']['rollbacktoken']

                parameters={'action': 'rollback',
                           'title': page.title(),
                           'user': page._rcinfo.get('user'),
                           'token': token,
                           'markbot': True}

                pywikibot.data.api.Request(
                    site=Site, parameters=parameters).submit()

            except Exception as e:
                print (u'Não consigo gravar a página')
