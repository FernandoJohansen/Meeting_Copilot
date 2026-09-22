from __future__ import annotations

from typing import Callable

_current_lang = "pt"
_listeners: list[Callable[[], None]] = []

STRINGS: dict[str, dict[str, str]] = {
    "pt": {
        "app_title": "Meeting Copilot — Assistente de Reuniões com IA",
        "ready_status": "Pronto. Configure os dispositivos de áudio e a chave da OpenAI em Configurações.",
        "settings_saved_status": "Configurações salvas.",
        "loading_model_status": "Carregando modelo Whisper local... (pode levar alguns segundos)",
        "model_load_failed_status": "Falha ao carregar modelo Whisper.",
        "error_loading_whisper_title": "Erro ao carregar Whisper",
        "no_audio_device_title": "Nenhum dispositivo de áudio",
        "no_audio_device_msg": "Selecione ao menos um dispositivo de áudio (microfone e/ou sistema) em Configurações.",
        "no_openai_key_status": "Sem chave da OpenAI configurada — transcrição ativa, mas sugestões de IA desativadas.",
        "meeting_running_status": "Reunião em andamento — capturando áudio e transcrevendo.",
        "meeting_stopped_status": "Reunião encerrada.",
        "suggestions_inactive_status": "Sugestões de IA não estão ativas (configure a chave da OpenAI).",
        "start_meeting_btn": "Iniciar reunião",
        "stop_meeting_btn": "Encerrar reunião",
        "suggest_now_btn": "Gerar sugestões agora",
        "settings_action": "Configurações",
        "transcript_label": "Transcrição ao vivo",
        "suggestions_label": "Sugestões de fala (IA)",
        "switching_to_light_status": "Alternando para modo Leve... reiniciando captura e modelo.",
        "switching_to_performance_status": "Alternando para modo Desempenho... reiniciando captura e modelo.",
        "light_mode_btn": "Leve",
        "performance_mode_btn": "Desempenho",
        "toolbar_title": "Controles",
        "you_source": "Você",
        "others_source": "Outros",
        "settings_title": "Configurações - Meeting Copilot",
        "llm_backend_label": "Motor de sugestões (IA):",
        "llm_backend_openai": "OpenAI (nuvem)",
        "llm_backend_ollama": "Ollama (local, sem API)",
        "api_key_label": "Chave da API OpenAI:",
        "show_password_btn": "Mostrar",
        "ollama_url_label": "Ollama - URL do servidor:",
        "ollama_url_tooltip": "Endereço do servidor Ollama local (padrão: http://localhost:11434/v1). Requer o Ollama instalado e rodando.",
        "ollama_model_label": "Ollama - nome do modelo:",
        "ollama_model_tooltip": "Nome do modelo já baixado no Ollama (ex: llama3.1, mistral, qwen2.5).",
        "performance_profile_label": "Perfil de desempenho:",
        "preset_light_label": "Leve (hardware fraco)",
        "preset_balanced_label": "Equilibrado",
        "preset_performance_label": "Desempenho",
        "preset_info_label": (
            "Os perfis ajustam modelo Whisper, duração dos blocos de áudio e uso de CPU de uma vez. "
            "Você também pode ajustar cada campo manualmente abaixo."
        ),
        "whisper_model_label": "Modelo Whisper (local):",
        "transcription_language_label": "Idioma da transcrição:",
        "lang_auto": "Detectar automaticamente",
        "lang_pt": "Português",
        "lang_en": "Inglês",
        "lang_es": "Espanhol",
        "mic_label": "Microfone (você):",
        "system_audio_label": "Áudio do sistema (outros / loopback):",
        "system_audio_none_option": "Nenhum (não capturar áudio do sistema)",
        "system_audio_no_monitor_tooltip": (
            "Nenhum monitor PipeWire/PulseAudio encontrado (via `pactl list sources short`). "
            "Verifique se o PipeWire está ativo."
        ),
        "system_audio_no_passthrough_tooltip": (
            "Dispositivo de passthrough 'pulse'/'pipewire' não encontrado no PortAudio. "
            "A captura de áudio do sistema não está disponível neste ambiente."
        ),
        "chunk_seconds_label": "Duração do bloco de áudio:",
        "chunk_seconds_tooltip": (
            "Blocos maiores = menos chamadas ao Whisper (economiza CPU), porém a transcrição "
            "demora mais para aparecer. Aumente em hardware fraco."
        ),
        "overlap_label": "Sobreposição entre blocos:",
        "overlap_tooltip": "Sobreposição entre blocos para não cortar palavras — quanto maior, mais CPU.",
        "cpu_threads_label": "Threads de CPU (Whisper):",
        "cpu_threads_tooltip": (
            "Limite de threads de CPU para a transcrição. Reduza para deixar núcleos livres "
            "para a interface e o restante do sistema em máquinas fracas."
        ),
        "cpu_threads_auto_text": "Automático (todos os núcleos)",
        "suggestion_interval_label": "Intervalo entre sugestões:",
        "suggestion_window_label": "Janela de transcrição p/ sugestões:",
        "meeting_context_label": "Contexto da reunião:",
        "meeting_context_placeholder": "Ex: pauta, objetivos da reunião, participantes...",
        "ui_language_label": "Idioma da interface:",
        "banner_text": "IA ativa nesta reunião — transcrição e sugestões (Meeting Copilot)",
        "copy_disclosure_btn": "Copiar aviso",
        "copy_disclosure_tooltip": "Copia um texto de transparência para colar no chat da reunião",
        "disclosure_text": (
            "Aviso: esta reunião está sendo assistida por uma IA (Meeting Copilot), que transcreve "
            "o áudio localmente e sugere pontos de fala. Nenhum dado é compartilhado sem meu conhecimento."
        ),
    },
    "en": {
        "app_title": "Meeting Copilot — AI Meeting Assistant",
        "ready_status": "Ready. Set up your audio devices and OpenAI key in Settings.",
        "settings_saved_status": "Settings saved.",
        "loading_model_status": "Loading local Whisper model... (this can take a few seconds)",
        "model_load_failed_status": "Failed to load Whisper model.",
        "error_loading_whisper_title": "Error loading Whisper",
        "no_audio_device_title": "No audio device",
        "no_audio_device_msg": "Select at least one audio device (microphone and/or system) in Settings.",
        "no_openai_key_status": "No OpenAI key configured — transcription is active, but AI suggestions are disabled.",
        "meeting_running_status": "Meeting in progress — capturing audio and transcribing.",
        "meeting_stopped_status": "Meeting ended.",
        "suggestions_inactive_status": "AI suggestions are not active (set your OpenAI key in Settings).",
        "start_meeting_btn": "Start meeting",
        "stop_meeting_btn": "End meeting",
        "suggest_now_btn": "Generate suggestions now",
        "settings_action": "Settings",
        "transcript_label": "Live transcript",
        "suggestions_label": "Talking points (AI)",
        "switching_to_light_status": "Switching to Light mode... restarting capture and model.",
        "switching_to_performance_status": "Switching to Performance mode... restarting capture and model.",
        "light_mode_btn": "Light",
        "performance_mode_btn": "Performance",
        "toolbar_title": "Controls",
        "you_source": "You",
        "others_source": "Others",
        "settings_title": "Settings - Meeting Copilot",
        "llm_backend_label": "Suggestion engine (AI):",
        "llm_backend_openai": "OpenAI (cloud)",
        "llm_backend_ollama": "Ollama (local, no API)",
        "api_key_label": "OpenAI API key:",
        "show_password_btn": "Show",
        "ollama_url_label": "Ollama - server URL:",
        "ollama_url_tooltip": "Local Ollama server address (default: http://localhost:11434/v1). Requires Ollama installed and running.",
        "ollama_model_label": "Ollama - model name:",
        "ollama_model_tooltip": "Name of a model already pulled in Ollama (e.g. llama3.1, mistral, qwen2.5).",
        "performance_profile_label": "Performance profile:",
        "preset_light_label": "Light (weak hardware)",
        "preset_balanced_label": "Balanced",
        "preset_performance_label": "Performance",
        "preset_info_label": (
            "Profiles adjust the Whisper model, audio block duration, and CPU usage all at once. "
            "You can also fine-tune each field manually below."
        ),
        "whisper_model_label": "Whisper model (local):",
        "transcription_language_label": "Transcription language:",
        "lang_auto": "Auto-detect",
        "lang_pt": "Portuguese",
        "lang_en": "English",
        "lang_es": "Spanish",
        "mic_label": "Microphone (you):",
        "system_audio_label": "System audio (others / loopback):",
        "system_audio_none_option": "None (don't capture system audio)",
        "system_audio_no_monitor_tooltip": (
            "No PipeWire/PulseAudio monitor found (via `pactl list sources short`). "
            "Check that PipeWire is running."
        ),
        "system_audio_no_passthrough_tooltip": (
            "The 'pulse'/'pipewire' passthrough device was not found in PortAudio. "
            "System audio capture is not available in this environment."
        ),
        "chunk_seconds_label": "Audio chunk duration:",
        "chunk_seconds_tooltip": (
            "Larger chunks mean fewer Whisper calls (saves CPU), but transcripts take longer to "
            "appear. Increase this on weak hardware."
        ),
        "overlap_label": "Overlap between chunks:",
        "overlap_tooltip": "Overlap between chunks so words aren't cut off — the larger, the more CPU it uses.",
        "cpu_threads_label": "CPU threads (Whisper):",
        "cpu_threads_tooltip": (
            "CPU thread limit for transcription. Lower it to leave cores free for the interface "
            "and the rest of the system on weak machines."
        ),
        "cpu_threads_auto_text": "Automatic (all cores)",
        "suggestion_interval_label": "Interval between suggestions:",
        "suggestion_window_label": "Transcript window for suggestions:",
        "meeting_context_label": "Meeting context:",
        "meeting_context_placeholder": "E.g.: agenda, meeting goals, participants...",
        "ui_language_label": "Interface language:",
        "banner_text": "AI active in this meeting — transcription and suggestions (Meeting Copilot)",
        "copy_disclosure_btn": "Copy notice",
        "copy_disclosure_tooltip": "Copies a transparency notice to paste into the meeting chat",
        "disclosure_text": (
            "Notice: this meeting is being assisted by an AI (Meeting Copilot), which transcribes "
            "audio locally and suggests talking points. No data is shared without my knowledge."
        ),
    },
}


def set_language(lang: str) -> None:
    global _current_lang
    if lang not in STRINGS:
        lang = "pt"
    _current_lang = lang
    for callback in list(_listeners):
        callback()


def get_language() -> str:
    return _current_lang


def tr(key: str) -> str:
    return STRINGS.get(_current_lang, STRINGS["pt"]).get(key, STRINGS["pt"].get(key, key))


def on_language_changed(callback: Callable[[], None]) -> None:
    _listeners.append(callback)
