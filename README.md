# Space Eye
https://github.com/user-attachments/assets/1ca37ec4-4120-441a-aee1-41a590b176be

# Sobre o projeto
O Space Eye é um web app desenvolvido em Python, utilizando Flask e Javascript. O objetivo é auxiliar na busca de imagens de satélite e o processamento das mesmas. No momento, além da lista de imagens disponíveis para a localidade, também é disponibilizado o recorte com base no polígono informado e também o Índice de Vegetação por Diferença Normalizada (NDVI) do raster selecionado.

As próximas atualizações serão relacionadas a optimização do processo de aquisição das imagens, com o objetivo de diminuir o tempo de download e processamento, além de incluir outras opções de satélites (Amazonas 1, por exemplo) e índices de vegetação (NDDI e NDWI).

# Instalação
Antes de tudo, crie uma conta nos serviços do INPE `http://queimadas.dgi.inpe.br/catalogo/explore`, em seguida, crie um arquivo `.env` na raiz do projeto e adicione o email cadastrado como variável no seguinte formato:
```
email_inpe = EMAIL_CADASTRADO
```

Crie um ambiente virtual e instale as libs presentes em `requirements.txt`:
```
python -m venv env
```

```
pip install -r requirements.txt
```

Para o mapa interativo, foi necessário realizar algumas alterações no plugin Draw da lib Folium. Portanto, copie o conteúdo do arquivo `draw.py` presente na raiz do projeto e cole o mesmo em: `...\env\Lib\site-packages\folium\plugins\draw.py`

Utilize o seguinte comando para iniciar a aplicação:
```
python __init__.py
```

# Tecnologias utilizadas
- Python
- Flask
- Javascript

- HTML
- CSS

- Rasterio
- Pandas e Geopandas

- Processamento de imagens multiespectrais
