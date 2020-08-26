# WolfgangBOT

WolfgangBOT é un bot que reverte vandalismo usando [ORES](https://mediawiki.org/wiki/ORES) para classificar las edições usando os parâmetros de `goodfaith` e `damaging` que a plataforma fornece.

Este bot está disponível através da licença MIT. Foi adaptado do SeroBOT operacional na es.wikipedia.org (ver https://github.com/dennistobar/serobot).

## Instalação
Este script requere o [pywikibot](https://mediawiki.org/wiki/pywikibot) para funcionar, pelo qual se devem seguir os pasos de instalação de pywikibot. Ademais requere [pandas](https://pandas.pydata.org/) para filtrar o log com mais eficiância e tornando-o mais fácil de entender.

Para as dependências, deve instalar-se o seguinte:
`pip3 install sseclient requests pandas`

Uma vez feito, deve-se clonar o repositório e ejecutar o script `python pwb.py <pasta>/bot-revertir` para começar a ejecução do bot.

## Colabora
Para cooperar com a construção do bot, pode fazer pull request ou reportar un [novo issue](https://github.com/themudo/WolfgangBOT/issues/new) em [github](https://github.com/themudo/WolfgangBOT.git)
