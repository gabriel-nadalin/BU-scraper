import os

from pathlib import Path

import scrapy

class BUSpider(scrapy.Spider):
    name = "buspider"
    start_urls = [
        "https://resultados.tse.jus.br/oficial/comum/config/ele-c.json",
    ]
    ufs = ["ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma", "mg", "ms", "mt", "pa", "pb", "pe", "pi", "pr", "rj", "rn", "ro", "rr", "rs", "sc", "se", "sp", "to", "zz"]

    # processa o arquivo de configuracao de eleicoes e constroi a url para os arquivos de configuracao de secao
    def parse(self, response):
        ciclo = response.json()['c']
        self.urlBase = f"https://resultados.tse.jus.br/oficial/{ciclo}/arquivo-urna/"

        for pleito in response.json()['pl']:
            cdPleito = pleito['cd']

            for uf in self.ufs:
                filename = f"{uf}-p{cdPleito.zfill(6)}-cs.json"
                url = self.urlBase + f"{cdPleito}/config/{uf}/{filename}"
                yield scrapy.Request(url=url, callback=self.parse_secoes_config)

    # processa os arquivos de configuracao de secao e controi a url para os arquivos auxiliares de secao
    def parse_secoes_config(self, response):
        cdPleito = response.json()['cdp']

        for abrangencia in response.json()['abr']:
            uf = abrangencia['cd'].lower()

            for municipio in abrangencia['mu']:
                cdMunicipio = municipio['cd'].zfill(5)

                for zona in municipio['zon']:
                    cdZona = zona['cd'].zfill(4)

                    for secao in zona['sec']:
                        nSecao = secao['ns'].zfill(4)

                        filename = f"p{cdPleito.zfill(6)}-{uf}-m{cdMunicipio}-z{cdZona}-s{nSecao}-aux.json"
                        url = self.urlBase + f"{cdPleito}/dados/{uf}/{cdMunicipio}/{cdZona}/{nSecao}/{filename}"
                        yield scrapy.Request(url=url, callback=self.parse_secoes_aux)

    # processa os arquivos auxiliares de secao e constroi a url para os BUs
    def parse_secoes_aux(self, response):
        urlSecao = response.url.rsplit('/', 1)[0] + '/'
        for hash in response.json()['hashes']:
            cdHash = hash['hash']
            st = hash['st']

            for arquivo in hash['nmarq']:
                if arquivo.endswith('.bu') or arquivo.endswith('.busa'):
                    url = urlSecao + f"{cdHash}/{arquivo}"
                    yield scrapy.Request(url=url, callback=self.parse_bu, meta={'status': st})

    # baixa os BUs
    def parse_bu(self, response):
        filename = response.url.split("/")[-1]
        dir = response.url.split('/')[3:-2]
        dir = "/".join(dir) + "/" + response.meta.get('status')
        os.makedirs(dir, exist_ok=True)
        Path(f"{dir}/{filename}").write_bytes(response.body)
        self.log(f"Saved file {filename}")