from pathlib import Path

import scrapy

class LogsSpider(scrapy.Spider):
    name = "logs"
    start_urls = [
        "https://resultados.tse.jus.br/oficial/comum/config/ele-c.json",
    ]
    ufs = ["ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma", "mg", "ms", "mt", "pa", "pb", "pe", "pi", "pr", "rj", "rn", "ro", "rr", "rs", "sc", "se", "sp", "to", "zz"]

    def parse(self, response):
        ciclo = response.json()['c']
        self.urlBase = f"https://resultados.tse.jus.br/oficial/{ciclo}/arquivo-urna/"

        for pleito in response.json()['pl']:
            cdPleito = pleito['cd']

            for uf in self.ufs:
                filename = f"{uf}-p{cdPleito.zfill(6)}-cs.json"
                url = self.urlBase + f"{cdPleito}/config/{uf}/{filename}"
                yield scrapy.Request(url=url, callback=self.parse_secoes_config)

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

    def parse_secoes_aux(self, response):
        urlSecao = response.url.rsplit('/', 1)[0] + '/'
        for hash in response.json()['hashes']:
            cdHash = hash['hash']

            for arquivo in hash['nmarq']:
                if arquivo.endswith('.bu'):
                    url = urlSecao + f"{cdHash}/{arquivo}"
                    yield scrapy.Request(url=url, callback=self.parse_bu)

    def parse_bu(self, response):
        filename = response.url.split("/")[-1]
        Path(f"bu_teste/{filename}").write_bytes(response.body)
        self.log(f"Saved file {filename}")


