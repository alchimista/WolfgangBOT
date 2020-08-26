# -*- coding: utf-8 -*

from __future__ import absolute_import, unicode_literals
import pywikibot
from pywikibot import pagegenerators, Bot
import sys
import os
import requests
import time
from datetime import datetime
import pandas as pd


class WolfgangBOT(Bot):

    """BOT que reverte a partir do ORES"""

    def __init__(self, generator, site=None, **kwargs):
        self.availableOptions.update({
            'gf': 0.085,
            'dm': 0.970,
            'wiki': 'ptwiki',
            'debug': False
        })
        """Constructor."""
        super(WolfgangBOT, self).__init__(**kwargs)
        self.generator = generator
        self.site = site
        if self.site.logged_in() == False:
            self.site.login()

    def run(self):
        for page in filter(lambda x: self.valid(x), self.generator):
            try:
                revisao, boa_fe, danosa, resultado = self.checkORES(page)
            except:
                continue
            data = [revisao, boa_fe, danosa, resultado,
                    page._rcinfo.get('user'), page.title(), datetime.utcnow().strftime('%Y%m%d%H%M%S'), int(datetime.utcnow().timestamp())]
            if self.getOption('debug'):
                print(data)
            self.do_log(data)
            self.do_reverse(page) if resultado == True else False
            if (self.site.family.name == 'wikipedia' and self.site.lang == 'pt'):
                self.check_user(page._rcinfo.get('user'),
                                page.title()) if resultado == True else False
                self.check_pagina(page.title()) if resultado == True else False

    def valid(self, page):
        """
        Determina se uma mudança é válida para poder invocar o endpoint do ORES
        Selecciona
        * só as edições,
        * o usuario não é bot
        * domínio 0 (principal)
        * o usuário não sou eu mesmo (WolfgangBOT)

        @param page: página a verificar
        @return true
        """
        return page._rcinfo.get('type') == 'edit' and page._rcinfo.get('bot') == False and page._rcinfo.get('namespace') in [0] and page._rcinfo.get('user') != self.site.username()

    def checkORES(self, page):
        headers = {
            'User-Agent': 'WolfgangBOT - an ORES counter vandalism tool'
        }
        wiki = self.getOption('wiki')
        revisao = page._rcinfo.get('revisao')
        ores = str(revisao.get('new'))
        url = 'https://ores.wikimedia.org/v3/scores/{0}/{1}'.format(wiki, ores)
        r = requests.get(url=url, headers=headers)
        data = r.json()
        try:
            goodfaith = data.get(wiki).get('scores').get(ores).get('goodfaith')
            damaging = data.get(wiki).get('scores').get(ores).get('damaging')
            boa_fe = goodfaith.get('score').get('probability').get('true')
            danosa = damaging.get('score').get('probability').get('true')
            return (ores, boa_fe, danosa, True if boa_fe < self.getOption('gf') or danosa > self.getOption('dm') else False)
        except:
            pywikibot.exception()

    def do_log(self, data):
        general = "{0}/log/{1}-general.log".format(os.path.dirname(
            os.path.realpath(__file__)), self.getOption('wiki'))
        positivo = "{0}/log/{1}-positivo.log".format(os.path.dirname(
            os.path.realpath(__file__)), self.getOption('wiki'))
        with open(general, encoding='utf-8', mode='a+') as arquivo:
            arquivo.write(u'\t'.join(map(lambda x: str(x), data)) + u'\n')
        if data[3] == True:
            with open(positivo, encoding='utf-8', mode='a+') as arquivo:
                arquivo.write(u'\t'.join(map(lambda x: str(x), data)) + u'\n')

    def check_user(self, usuario, pagina):
        positivo = "{0}/log/{1}-positivo.log".format(os.path.dirname(
            os.path.realpath(__file__)), self.getOption('wiki'))
        df_reversas = pd.read_csv(positivo, header=None, delimiter='\t')
        user = df_reversas[4] == usuario
        page = df_reversas[5] == pagina
        past = (int(datetime.utcnow().timestamp()) -
                df_reversas[7]) < (60*60*4)  # 4 horas
        rows = df_reversas[user & page & past]
        User = pywikibot.User(self.site, usuario)
        if (len(rows) == 2 and User.isAnonymous() == False):
            if self.getOption('debug'):
                print('Avisando a ', usuario)
            talk = pywikibot.Page(self.site, title=usuario, ns=3)
            talk.text += u"\n{{subst:Av-teste|2|" + pagina + "}} ~~~~"
            talk.save(
                comment=u'Aviso sobre testes a usuário depois de reversões consecutivas')
            with open(os.path.dirname(os.path.realpath(__file__)) + '/log/discusiones.log', 'a+') as arquivo:
                arquivo.write('\t'.join(map(lambda x: str(x), [usuario, pagina, datetime.utcnow(
                ).strftime('%Y%m%d%H%M%S'), int(datetime.utcnow().timestamp())])) + '\n')
            return
        rows = df_reversas[user & past]
        if (len(rows) == 4):
            if self.getOption('debug'):
                print('VEC a ', usuario)
            with open(os.path.dirname(os.path.realpath(__file__)) + '/log/vec.log', 'a+') as arquivo:
                arquivo.write('\t'.join(map(lambda x: str(x), [usuario, datetime.utcnow(
                ).strftime('%Y%m%d%H%M%S'), int(datetime.utcnow().timestamp())])) + '\n')

            vec = pywikibot.Page(self.site, title='Vandalismo em curso', ns=4)
            tpl = u'{{subst:'
            tpl += 'bloquear'
            tpl += u'|1='+usuario
            tpl += u'|2=Reversões: ' + \
                (', '.join(
                    map(lambda x: u'[[Special:Diff/'+str(x)+'|diff: '+str(x)+']]', rows[0])))
            tpl += u'}}'
            vec.text += "\n"+tpl
            try:
                vec.save(comment=u'Reportando o usuário [[Special:Contributions/' +
                         usuario+'|'+usuario+']] por possível vandalismo')
            except:
                pass
        return

    def check_pagina(self, pagina):
        positivo = "{0}/log/{1}-positivo.log".format(os.path.dirname(
            os.path.realpath(__file__)), self.getOption('wiki'))
        df_reversas = pd.read_csv(positivo, header=None, delimiter='\t')
        page = df_reversas[5] == pagina
        past = (int(datetime.utcnow().timestamp()) -
                df_reversas[7]) < (60*60*4)  # 4 horas
        users = df_reversas[page & past][4].nunique()

        rows = df_reversas[page & past]
        if (len(rows) < 6 or users < 2):
            return
        if self.getOption('debug'):
            print('Pedido de proteção de página ', pagina)

        tabp = pywikibot.Page(
            self.site, title='Pedidos/Proteção', ns=4)
        if (tabp.get().find('{{{{a|{0}}}}}'.format(pagina)) != -1):
            return
        tpl = '{{{{subst:Proteger|pagina={0}|razão=Reversões consecutivas pelo WolfgangBOT. ~~~~}}}}'.format(
            pagina)
        tabp.text += "\n"+tpl
        try:
            tabp.save(
                comment=u'Pedindo proteção de {0} por reversões consecutivas'.format(pagina))
        except:
            pass
        return

    def do_reverse(self, page):
        if self.getOption('debug'):
            print('>> Reversão', page._rcinfo.get('user'), page.title())
        try:
            token = pywikibot.data.api.Request(site=self.site, parameters={
                                               'action': 'query', 'meta': 'tokens', 'type': 'rollback'}).submit()['query']['tokens']['rollbacktoken']

            parameters = {'action': 'rollback',
                          'title': page.title(),
                          'user': page._rcinfo.get('user'),
                          'token': token,
                          'markbot': True}

            pywikibot.data.api.Request(
                site=self.site, parameters=parameters).submit()
            return
        except Exception as e:
            print(u'Não consigo reverter a página ', e)


def main(*args):
    """
    Processa os parâmetros desde a linha de comandos

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    opts = {}
    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        if arg.startswith('-gf:'):
            opts['gf'] = float(arg[4:])
        elif arg.startswith('-dm:'):
            opts['dm'] = float(arg[4:])
        elif arg.startswith('-wiki:'):
            opts['wiki'] = arg[6:]
        elif arg.startswith('--debug'):
            opts['debug'] = True

    site = pywikibot.Site()
    if 'wiki' in opts and opts['wiki'] != 'ptwiki':
        lang = opts['wiki'][0:2]
        family = opts['wiki'][2:]
        site = pywikibot.Site(lang, family)

    bot = WolfgangBOT(pagegenerators.LiveRCPageGenerator(site),
                  site=site, **opts)
    bot.run()


if __name__ == '__main__':
    main()
