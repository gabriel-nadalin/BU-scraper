# BU Scraper

Esse script realiza o download dos Boletins de Urna (BUs) gerados pela urnas eletrônicas durante uma eleição, segundo instruções diponíveis [aqui](https://www.tse.jus.br/eleicoes/informacoes-tecnicas-sobre-a-divulgacao-de-resultados).

## Para rodar em um container
é necessário instalar o docker-compose:\
`apt install docker-compose`,\
executar o comando\
`docker-compose run scraper`\
e seguir as instruções

## Para rodar em Python nativo
é necessário instalar o Scrapy:\
`pip install scrapy`\
Com o Scrapy instalado, basta executar o comando\
`python3 baixar_BUs.py`\
e seguir as instruções

## TO-DO
 - Log de metadados dos BUs em banco de dados
