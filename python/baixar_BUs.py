import os
import sys
import psutil
import socket
import itertools
import cProfile
import pstats
import io

from pathlib import Path
from pymongo import MongoClient
from datetime import datetime

import scrapy
from scrapy.crawler import CrawlerProcess

import logging

# remove mensagens de debug do pymongo
logging.getLogger("pymongo").setLevel(logging.CRITICAL)


class BUSpider(scrapy.Spider):
    name = "buspider"
    start_urls = [
        "https://resultados.tse.jus.br/oficial/comum/config/ele-c.json",
    ]
    
    def __init__(self, diretorio, pleito=None, *args, **kwargs):
        super(BUSpider, self).__init__(*args, **kwargs)
        self.diretorio = diretorio
        self.pleito = pleito
        self.ufs = ["ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma", "mg", "ms", "mt", "pa", "pb", "pe", "pi", "pr", "rj", "rn", "ro", "rr", "rs", "sc", "se", "sp", "to", "zz"]
        self.entradas_bu = []

        mongo_host = os.getenv("MONGO_HOST", "mongodb://localhost:27017/")
        client = MongoClient(mongo_host)
        db = client["bu"]
        self.colecao = db[self.diretorio]

        avail_bind_addr = [addr.address
                                for addr in itertools.chain(*psutil.net_if_addrs().values())
                                if addr.family == socket.AF_INET6 and not addr.address.startswith('f') and addr.address != '::1']
        self.log(f'Available bind address: {avail_bind_addr}')
        self.bind_addr_iter = itertools.cycle(avail_bind_addr)

    # processa o arquivo de configuracao de eleicoes e constroi a url para os arquivos de configuracao de secao
    def parse(self, response):
        ciclo = response.json()['c']
        self.urlBase = f"https://resultados.tse.jus.br/oficial/{ciclo}/arquivo-urna/"
        pleitos = [pleito['cd'] for pleito in response.json()['pl']]

        escolha = self.pleito or ""

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
                        yield scrapy.Request(url=url, callback=self.parse_secoes_config, meta={'bindaddress': (next(self.bind_addr_iter), 0)})

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
                    yield scrapy.Request(url=url, callback=self.parse_secoes_config, meta={'bindaddress': (next(self.bind_addr_iter), 0)})

            elif escolha != "sair":
                escolha = ""
                print("Pleito invalido!")

    # processa os arquivos de configuracao de secao e controi a url para os arquivos auxiliares de secao
    def parse_secoes_config(self, response):
        cdPleito = response.json()['cdp']

        for abrangencia in response.json()['abr']:
            uf = abrangencia['cd'].lower()
            dir = self.diretorio + "/" + uf + "/"
            os.makedirs(dir, exist_ok=True)

            for municipio in abrangencia['mu']:
                cdMunicipio = municipio['cd'].zfill(5)

                for zona in municipio['zon']:
                    cdZona = zona['cd'].zfill(4)

                    for secao in zona['sec']:
                        if 'nsp' not in secao:
                            nSecao = secao['ns'].zfill(4)

                            filename = f"p{cdPleito.zfill(6)}-{uf}-m{cdMunicipio}-z{cdZona}-s{nSecao}-aux.json"
                            url = self.urlBase + f"{cdPleito}/dados/{uf}/{cdMunicipio}/{cdZona}/{nSecao}/{filename}"
                            yield scrapy.Request(url=url, callback=self.parse_secoes_aux, meta={'uf': uf, 'bindaddress': (next(self.bind_addr_iter), 0)})

    # processa os arquivos auxiliares de secao e constroi a url para os BUs
    def parse_secoes_aux(self, response):
        urlSecao = response.url.rsplit('/', 1)[0] + '/'
        for hash in response.json()['hashes']:
            cdHash = hash['hash']
            data = hash['dr']
            hora = hash['hr']
            status = hash['st']
            timestamp_string = f"{data} {hora}"
            timestamp = datetime.strptime(timestamp_string, "%d/%m/%Y %H:%M:%S")

            for arquivo in hash['arq']:
                nmArquivo = arquivo['nm']
                tpArquivo = arquivo['tp']

                if tpArquivo == "bu" or tpArquivo == "busa":
                    url = urlSecao + f"{cdHash}/{nmArquivo}"
                    uf = response.meta.get("uf")
                    yield scrapy.Request(url=url, callback=self.parse_bu, meta={'uf': uf, 'timestamp': timestamp, 'status': status, 'bindaddress': (next(self.bind_addr_iter), 0)})

                    # teste para o simulado, que nao gera os BUs
                    # dir = self.diretorio + "/"
                    # Path(f"{dir}/{nmArquivo}").write_bytes("teste".encode())
                    # self.log(f"Arquivo salvo: {nmArquivo}")

    # baixa os BUs
    def parse_bu(self, response):
        filename = response.url.split("/")[-1]
        dir = self.diretorio + "/" + response.meta.get("uf") + "/"

        Path(f"{dir}/{filename}").write_bytes(response.body)
        # self.log(f"Arquivo salvo: {filename}")

        timestamp = response.meta.get("timestamp")
        status = response.meta.get("status")

        # self.colecao.insert_one({"arquivo": filename, "url": response.url, "timestamp": timestamp, "status": status})

        self.entradas_bu.append({"arquivo": filename, "url": response.url, "timestamp": timestamp, "status": status})
        if len(self.entradas_bu) >= 500:
            self.colecao.insert_many(self.entradas_bu)
            self.entradas_bu = []


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Uso: python3 baixar_BUs.py <diretorio_destino> [pleito=<id>]')
        exit(1)

    dir = sys.argv[1]
    os.makedirs(dir, exist_ok=True)

    pleito = None
    if len(sys.argv) > 2 and sys.argv[2].startswith("pleito="):
        pleito = sys.argv[2].split("=")[1]
    
    process = CrawlerProcess(settings={
        'CONCURRENT_REQUESTS': 4000,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4000,
        'DOWNLOAD_DELAY': 0.0001,
        'AUTOTHROTTLE_ENABLED': False,
        # 'AUTOTHROTTLE_START_DELAY': 0.03,
        # 'AUTOTHROTTLE_MAX_DELAY': 1.0,
        "DNS_RESOLVER": "resolver.ForceIPv6Resolver",
        'LOG_LEVEL': 'INFO',
        'REACTOR_THREADPOOL_MAXSIZE': 100
    })
    scraper = process.crawl(BUSpider, diretorio=dir, pleito=pleito)
    process.start()