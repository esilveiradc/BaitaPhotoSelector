# Baita Photo Selector

**Versão atual: 0.1-alpha**

Software em Python para seleção inteligente de fotografias, criado para ajudar fotógrafos a revisar grandes volumes de imagens e separar fotos tremidas, desfocadas, borradas, escuras, estouradas, com olhos fechados ou muito parecidas.

> Status atual: versão Alpha para testes e validação. Ainda não é uma versão estável de produção.

## Recursos da versão 0.1-alpha

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
pyinstaller --onefile --windowed --name "Baita Photo Selector Pro v0.1-alpha" baita_photo_selector_pro_v0.1-alpha.py
```

O executável será gerado em:

```text
dist/Baita Photo Selector v0.1.exe
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

## Changelog resumido

### 0.1-alpha

Primeira versão pública de desenvolvimento do Baita Photo Selector.

Inclui a base da interface, análise de nitidez, tremida, exposição ruim, olhos fechados, fotos parecidas, perfis configuráveis, revisão visual, zoom 100%, relatório CSV e suporte inicial a RAW.

## Observação

A análise automática ajuda na triagem, mas não substitui totalmente a revisão humana. Em eventos, corridas e retratos, a foto tecnicamente mais nítida nem sempre é a melhor expressão, pose ou composição.

## Roadmap

### Próximas versões previstas

- `v0.2-alpha`: correções, testes com lotes reais e ajuste dos limites de análise.
- `v0.5-beta`: cache, configurações persistentes, miniaturas em grade e melhorias de comparação.
- `v1.0-stable`: versão testada, empacotada e pronta para uso profissional.

## Licença

MIT License
