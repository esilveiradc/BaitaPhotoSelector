# Baita Photo Selector

Software em Python para seleção inteligente de fotografias, criado para ajudar fotógrafos a revisar grandes volumes de imagens e separar fotos tremidas, desfocadas, borradas, escuras, estouradas, com olhos fechados ou parecidas.

## Recursos

- Interface gráfica com Tkinter
- Detecção de fotos desfocadas
- Detecção de fotos tremidas/borradas
- Detecção de fotos escuras
- Detecção de fotos estouradas
- Detecção de olhos fechados com MediaPipe
- Detecção de fotos parecidas
- Sugestão automática da foto mais nítida do grupo
- Comparação lado a lado de fotos parecidas
- Zoom 100%
- Modo copiar ou mover
- Desfazer ações da sessão
- Relatório CSV opcional
- Suporte JPG, JPEG, PNG, BMP e WEBP
- Suporte opcional RAW: CR2, CR3, NEF, ARW, DNG, RAF, ORF e RW2
- Perfis configuráveis, com perfil inicial `Padrao`

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
python baita_photo_selector_pro.py
```

## Gerar executável Windows

```bash
pyinstaller --onefile --windowed --name "Baita Photo Selector" baita_photo_selector_pro.py
```

O executável será gerado na pasta:

```text
dist/
```

## Observação

A análise automática ajuda muito na triagem, mas não substitui 100% a revisão humana. Em eventos, corrida e retratos, a foto tecnicamente mais nítida nem sempre é a melhor expressão ou melhor momento.

## Licença

MIT License
