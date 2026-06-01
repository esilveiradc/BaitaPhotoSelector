# Baita Photo Selector

**Versão atual: 1.0**

Software em Python para seleção inteligente de fotografias, criado para ajudar fotógrafos a revisar grandes volumes de imagens e separar fotos tremidas, desfocadas, borradas, escuras, estouradas, com olhos fechados ou muito parecidas.

## Recursos da versão 1.0

- Interface gráfica com Tkinter
- Perfil inicial configurável: `Padrao`
- Adicionar, editar e remover perfis personalizados
- Detecção de fotos desfocadas
- Detecção de fotos tremidas/borradas
- Análise por região central
- Análise por região provável do assunto principal
- Detecção de fotos escuras
- Detecção de fotos estouradas
- Detecção de olhos fechados com MediaPipe
- Detecção de fotos parecidas
- Sugestão automática da foto mais nítida do grupo
- Comparação lado a lado de fotos parecidas
- Botão para manter uma foto e enviar as outras do grupo para revisão/ruins
- Zoom 100%
- Modo copiar ou mover
- Desfazer ações da sessão
- Relatório CSV opcional
- Suporte JPG, JPEG, PNG, BMP e WEBP
- Suporte opcional RAW: CR2, CR3, NEF, ARW, DNG, RAF, ORF e RW2

## Instalação

Recomendado usar Python 3.10 ou superior.

```bash
pip install -r requirements.txt
```

## Execução

```bash
python baita_photo_selector_pro.py
```

## Gerar executável Windows

Instale o PyInstaller:

```bash
pip install pyinstaller
```

Gere o executável:

```bash
pyinstaller --onefile --windowed --name "Baita Photo Selector" baita_photo_selector_pro.py
```

O executável será gerado em:

```text
dist/Baita Photo Selector.exe
```

## Como usar

1. Abra o programa.
2. Selecione se deseja incluir arquivos RAW.
3. Clique em **Selecionar pasta**.
4. Clique em **Analisar**.
5. Revise as fotos suspeitas.
6. Use **Manter**, **Copiar/Mover para ruins**, **Comparar parecidas** ou **Zoom 100%**.

## Pastas geradas

Quando o modo copiar estiver ativado:

```text
FOTOS_RUINS_COPIAS
```

Quando o modo mover estiver ativado:

```text
FOTOS_RUINS
```

## Relatório

Quando ativado, o sistema gera:

```text
relatorio_baita_photo_selector.csv
```

O relatório inclui score, motivos, nitidez, exposição, motion blur e grupos de fotos parecidas.

## Changelog

### 1.0

Primeira versão pública do Baita Photo Selector.

Inclui detecção de nitidez, tremida, exposição ruim, olhos fechados, fotos parecidas, perfis configuráveis, revisão visual, zoom 100%, relatório CSV e suporte inicial a RAW.

## Observação

A análise automática ajuda na triagem, mas não substitui totalmente a revisão humana. Em eventos, corridas e retratos, a foto tecnicamente mais nítida nem sempre é a melhor expressão, pose ou composição.

## Licença

MIT License
