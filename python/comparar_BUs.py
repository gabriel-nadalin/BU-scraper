import os
import filecmp
import sys

def compara_diretorios(dir1, dir2):
    arquivos1 = set(os.listdir(dir1))
    arquivos2 = set(os.listdir(dir2))
    
    # arquivos apenas em dir1
    dif1 = arquivos1 - arquivos2
    # arquivos apenas em dir2
    dif2 = arquivos2 - arquivos1
    # arquivos comuns a ambos
    arquivos_comuns = arquivos1 & arquivos2

    if dif1:
        print(f"Arquivos presentes apenas em {dir1}:")
        for arquivo in dif1:
            print(f"  {arquivo}")
    
    if dif2:
        print(f"\nArquivos presentes apenas em {dir2}:")
        for arquivo in dif2:
            print(f"  {arquivo}")
    
    # comparando arquivos em comum
    for arquivo in arquivos_comuns:
        caminho1 = os.path.join(dir1, arquivo)
        caminho2 = os.path.join(dir2, arquivo)
        
        if os.path.isfile(caminho1) and os.path.isfile(caminho2):
            if not filecmp.cmp(caminho1, caminho2, shallow=False):
                print(f"{arquivo}: diferenca encontrada!")
        elif os.path.isdir(caminho1) and os.path.isdir(caminho2):
            compara_diretorios(caminho1, caminho2)
        else:
            print(f"{arquivo}: tipos incompativeis entre arquivos")
            
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python3 comparar_BUs.py <diretorio_1> <diretorio_2>")
        sys.exit(1)
    
    dir1 = sys.argv[1]
    dir2 = sys.argv[2]

    compara_diretorios(dir1, dir2)
