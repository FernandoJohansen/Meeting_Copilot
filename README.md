# Meeting Copilot: Assistente de Reuniões com IA

[Português](README.md) | [English](README.en.md)

Aplicação desktop em Python (PySide6) que acompanha reuniões em tempo real:
transcreve o áudio localmente (faster-whisper) e sugere pontos de fala usando
um modelo de linguagem, na nuvem (OpenAI) ou 100% local (Ollama), com uso
transparente aos participantes.

## Como funciona

- **Captura de áudio**: dois fluxos independentes, seu microfone ("Você") e
  o áudio do sistema/loopback ("Outros", ex. os demais participantes em uma
  chamada de Zoom/Meet/Teams).
- **Transcrição**: 100% local via [faster-whisper](https://github.com/SYSTRAN/faster-whisper),
  o áudio não é enviado a nenhum servidor para transcrever.
- **Sugestões**: a transcrição recente é enviada a um modelo de linguagem
  para gerar pontos de fala curtos e acionáveis (perguntas, riscos, próximos
  passos). Duas opções, escolhidas em Configurações:
  - **OpenAI (nuvem)**: requer uma chave de API e créditos na conta.
  - **Ollama (local, sem API)**: roda um LLM open-source na sua própria
    máquina, sem enviar nenhum texto a terceiros e sem custo por uso.
- **Transparência**: enquanto a reunião está ativa, um banner sempre-visível
  é exibido na tela (útil se você compartilhar a tela) informando que uma IA
  está assistindo a reunião, com um botão para copiar um aviso pronto para
  colar no chat.
- **Sem sugestões também é uma opção**: se você não configurar nem OpenAI
  nem Ollama, o app continua funcionando normalmente só com a transcrição
  local; o painel de sugestões simplesmente fica vazio.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Interface: modo de desempenho e idioma

A barra de ferramentas tem dois switches:

- **Leve / Desempenho**: alterna instantaneamente entre um perfil de
  transcrição leve (modelo `tiny`, blocos maiores, menos threads de CPU) e
  um perfil de desempenho (modelo `small`, blocos menores, menor latência).
  Se uma reunião estiver em andamento, a captura e o modelo são reiniciados
  automaticamente com o novo perfil. Um terceiro perfil "Equilibrado" fica
  disponível em Configurações.
- **PT / EN**: troca o idioma de toda a interface (títulos, botões,
  mensagens de status, banner de transparência) instantaneamente, sem
  precisar reiniciar o app. A preferência é salva e restaurada na próxima
  vez que o app for aberto.

> Nota: esse idioma da interface é independente do **idioma da
> transcrição** (Configurações → "Idioma da transcrição"), que define em
> qual idioma o Whisper deve reconhecer a fala.

## Usando o Ollama (sugestões 100% locais)

1. Instale o Ollama: <https://ollama.com>
2. Baixe um modelo, por exemplo:
   ```bash
   ollama pull llama3.1        # bom equilíbrio qualidade/tamanho
   ollama pull qwen2.5:3b      # mais leve, para hardware fraco
   ```
3. Em **Configurações**, mude "Motor de sugestões (IA)" para
   **Ollama (local, sem API)** e confirme a URL do servidor (padrão
   `http://localhost:11434/v1`) e o nome do modelo baixado.
4. Nenhuma chave de API é necessária nesse modo.

## Otimizando para hardware fraco

O maior custo de CPU do app é a transcrição local (Whisper). Ajustes, do
mais para o menos impactante:

1. **Capture só o microfone.** Sem o áudio do sistema, o modelo roda uma
   única vez por bloco em vez de duas, cortando o uso de CPU da transcrição
   pela metade. Deixe "Áudio do sistema" como "Nenhum" em Configurações.
2. **Use o switch Leve na barra de ferramentas** (ou o perfil "Leve" em
   Configurações): modelo `tiny`, blocos de 10s, 2 threads de CPU.
   Indicado para notebooks fracos, mini-PCs ou quando o app roda junto com
   a chamada de vídeo.
3. **Aumente a duração do bloco de áudio.** Blocos maiores geram menos
   chamadas ao Whisper por minuto (menos overhead fixo por chamada), ao
   custo de a transcrição demorar mais para aparecer na tela.
4. **Limite as threads de CPU.** Por padrão (`0`) a transcrição usa todos
   os núcleos disponíveis, o que pode deixar a interface e o restante do
   sistema travando durante a transcrição em máquinas com poucos núcleos.
   Reduzir para 1 ou 2 threads deixa núcleos livres para o resto do sistema,
   à custa de transcrição mais lenta.
5. **`whisper_compute_type: int8`** (padrão) já é a configuração de menor
   uso de memória/CPU para rodar em CPU; não há necessidade de alterar,
   a menos que você tenha GPU NVIDIA (nesse caso, veja `whisper_device` no
   arquivo de configuração).
6. **Se usar Ollama, prefira um modelo pequeno** (ex. `qwen2.5:3b` ou
   `llama3.2:3b`): ele roda ao mesmo tempo que o Whisper e disputa CPU/RAM
   com ele.

A transcrição usa VAD (detecção de atividade de voz) para pular trechos de
silêncio automaticamente; a maior parte do custo real de CPU acontece só
quando alguém está falando.

## Configuração de áudio no Linux (PipeWire/PulseAudio)

Para capturar o áudio dos outros participantes (loopback), a aplicação lista
os dispositivos de entrada disponíveis e tenta detectar automaticamente um
dispositivo "monitor" (ex.: `Monitor of Built-in Audio`). Se nenhum aparecer:

```bash
pactl list sources short   # procure por um source terminado em ".monitor"
```

Se não existir nenhum, você pode habilitar um no PipeWire/PulseAudio (ex. via
`pavucontrol`, aba "Recording", ou criando um sink de monitor). Selecione o
dispositivo de microfone e o de sistema em **Configurações** dentro do app.

## Uso

```bash
python -m meeting_copilot
```

1. Abra **Configurações**, escolha o motor de sugestões (OpenAI ou Ollama)
   e informe o necessário (chave de API, ou URL/modelo do Ollama), o
   tamanho do modelo Whisper (comece com `small` para equilíbrio entre
   velocidade e qualidade em CPU) e os dispositivos de áudio.
2. Clique em **Iniciar reunião**. O modelo Whisper é carregado (pode levar
   alguns segundos) e a captura de áudio + transcrição começam.
3. O banner de transparência aparece automaticamente; use "Copiar aviso"
   para informar os participantes de que uma IA está em uso.
4. Sugestões de fala aparecem periodicamente no painel direito; use
   **Gerar sugestões agora** para forçar uma atualização.
5. Use os switches **Leve/Desempenho** e **PT/EN** na barra de ferramentas
   a qualquer momento.
6. Clique em **Encerrar reunião** para parar tudo.

## Privacidade e ética

- A transcrição roda localmente; nenhum áudio é enviado a terceiros.
- Se você usar o motor OpenAI, apenas trechos de texto da transcrição (não
  o áudio) são enviados para gerar sugestões. Com o motor Ollama, nem isso
  sai da sua máquina.
- O banner de transparência é exibido sempre que a captura está ativa; **use
  esta ferramenta de forma ética**: informe verbalmente ou pelo chat que uma
  IA está assistindo a reunião antes de usá-la, especialmente em chamadas
  com terceiros.
- A chave de API (quando usada) é armazenada em texto simples no arquivo de
  configuração local (`~/.config/MeetingCopilot/config.json`).

## Estrutura do projeto

```
meeting_copilot/
  audio/       captura de microfone e áudio do sistema (sounddevice)
  stt/         transcrição local com faster-whisper
  llm/         geração de sugestões via OpenAI ou Ollama
  core/        configuração e armazenamento da transcrição
  ui/          janela principal, banner de transparência, configurações, i18n
```
