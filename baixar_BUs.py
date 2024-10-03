import os
import sys

from pathlib import Path

import scrapy
from scrapy.crawler import CrawlerProcess

class BUSpider(scrapy.Spider):
    name = "buspider"
    start_urls = [
        "https://resultados-sim.tse.jus.br/simulado/comum/config/ele-c.json",
    ]
    ufs = ["ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma", "mg", "ms", "mt", "pa", "pb", "pe", "pi", "pr", "rj", "rn", "ro", "rr", "rs", "sc", "se", "sp", "to", "zz"]

    # processa o arquivo de configuracao de eleicoes e constroi a url para os arquivos de configuracao de secao
    def parse(self, response):
        ciclo = response.json()['c']
        self.urlBase = f"https://resultados-sim.tse.jus.br/simulado/{ciclo}/arquivo-urna/"
        pleitos = [pleito['cd'] for pleito in response.json()['pl']]
        escolha = ""

        # checa se pleito foi passado como argumento
        if len(sys.argv) > 2 and sys.argv[2].startswith("pleito="):
            escolha = sys.argv[2].split("=")[1]

        while escolha != "sair":
            if escolha == "":
                print(f"\nPleitos disponiveis: {pleitos}")
                escolha = input(f"Escolha um pleito (ou \'ajuda\'): ")

            if escolha == "todos":
                escolha = "sair"
                for pleito in pleitos:
                    for uf in self.ufs:
                        filename = f"{uf}-p{pleito.zfill(6)}-cs.json"
                        url = self.urlBase + f"{pleito}/config/{uf}/{filename}"
                        yield scrapy.Request(url=url, callback=self.parse_secoes_config)

            elif escolha == "ajuda":
                escolha = ""
                print("\ncomandos:")
                print("\'ajuda\' - mostra menu de ajuda")
                print("\'todos\' - baixa os BUs de todos os pleitos disponiveis")
                print("\'sair\' - encerra o programa")

            elif escolha in pleitos:
                pleito = escolha
                escolha = "sair"
                for uf in self.ufs:
                    filename = f"{uf}-p{pleito.zfill(6)}-cs.json"
                    url = self.urlBase + f"{pleito}/config/{uf}/{filename}"
                    yield scrapy.Request(url=url, callback=self.parse_secoes_config)

            elif escolha != "sair":
                escolha = ""
                print("Pleito invalido!")

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
            dr = hash['dr']
            hr = hash['hr']
            st = hash['st']

            for arquivo in hash['arq']:
                nmArquivo = arquivo['nm']
                tpArquivo = arquivo['tp']

                if tpArquivo == "bu" or tpArquivo == "busa":
                    url = urlSecao + f"{cdHash}/{nmArquivo}"
                    yield scrapy.Request(url=url, callback=self.parse_bu, meta={'data': dr, 'horario': hr, 'status': st})

                    # teste para o simulado, que nao gera os BUs
                    dir = self.settings.get('diretorio') + "/"
                    Path(f"{dir}/{nmArquivo}").write_bytes("teste".encode())
                    self.log(f"Arquivo salvo: {nmArquivo}")

    # baixa os BUs
    def parse_bu(self, response):
        filename = response.url.split("/")[-1]
        dir = self.settings.get('diretorio') + "/"
        Path(f"{dir}/{filename}").write_bytes(response.body)
        self.log(f"Arquivo salvo: {filename}")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print('Uso: python3 baixar_BUs.py <diretorio_destino> [pleito=<id>]')
        exit(1)
        
    dir = sys.argv[1]
    os.makedirs(dir, exist_ok=True)
    
    process = CrawlerProcess(settings={'diretorio': dir})
    process.crawl(BUSpider)
    process.start()