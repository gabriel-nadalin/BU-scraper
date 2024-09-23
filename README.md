## BU Scraper

Esse script realiza o download dos Boletins de Urna (BUs) gerados pela urnas eletrônicas durante uma eleição, segundo instruções diponíveis [aqui](https://www.tse.jus.br/eleicoes/informacoes-tecnicas-sobre-a-divulgacao-de-resultados).\
\
Para executá-lo é necessário instalar o Scrapy:\
`pip install scrapy`\
\
Com o Scrapy instalado, basta executar o comando\
`scrapy crawl boletins_spider.py`\
e o script fará o download de todos os BUs.
