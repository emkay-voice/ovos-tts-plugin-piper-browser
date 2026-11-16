"""ovos-tts-plugin-piper-browser: Piper voices made on the phone itself (issue #3).

On a device ovos-tts-plugin-piper runs Piper with onnxruntime and espeak-ng.
Neither installs in Pyodide, so this plugin hands the sentence to
web/piper.js in the same worker, which runs both as WebAssembly, and gets
a WAV back. Nothing leaves the phone except the one download of the voice
(from rhasspy's piper-voices on Hugging Face) the first time it is used.

Chosen like any TTS plugin (`tts.module`). Until the chosen voice has
downloaded, `tts.fallback_module` speaks (emkay_mobile/speech.py). Its config, as the device
plugin's: `voice` (a piper-voices name, e.g. "da_DK-talesyntese-medium");
without one, the voice for OVOS' language in VOICES below.
"""
from ovos_plugin_manager.templates.tts import TTS
from ovos_utils import classproperty

PLUGIN = "ovos-tts-plugin-piper-browser"

#: one voice per language Emkay has intents for (medium quality, ~63 MB
#: each, where piper-voices has one); a language without one here falls
#: back to the TTS plugin in `tts.fallback_module`
VOICES = {
    "en-us": "en_US-lessac-medium",
    "en-gb": "en_GB-alba-medium",
    "da-dk": "da_DK-talesyntese-medium",
    "de-de": "de_DE-thorsten-medium",
    "es-es": "es_ES-davefx-medium",
    "fr-fr": "fr_FR-siwis-medium",
    "it-it": "it_IT-paola-medium",
    "nl-nl": "nl_NL-pim-medium",
    "pt-pt": "pt_PT-tugão-medium",
    "pt-br": "pt_BR-faber-medium",
    "ca-es": "ca_ES-upc_ona-medium",
    "eu-es": "eu_ES-antton-medium",
}


def voice_for(lang: str):
    lang = (lang or "en-us").lower()
    return VOICES.get(lang) or next((v for k, v in VOICES.items() if k.split("-")[0] == lang.split("-")[0]), None)


class PiperBrowserTTS(TTS):
    """Piper in the page's worker (web/piper.js)."""

    def __init__(self, config=None, *args, **kwargs):
        super().__init__(config=config, audio_ext="wav", *args, **kwargs)

    def get_tts(self, sentence, wav_file, lang=None, voice=None):
        import js
        from pyodide.ffi import run_sync
        lang = lang or self.lang
        voice = voice if voice and voice != "default" else self.config.get("voice") or voice_for(lang)
        if not voice:
            raise ValueError(f"no Piper voice for {lang}")
        if not run_sync(js.emkayPiper.ready(voice)):
            # downloading now; speech.py lets tts.fallback_module say this one
            raise RuntimeError(f"the Piper voice {voice} is still downloading")
        data = run_sync(js.emkayPiper.synth(sentence, voice, int(self.config.get("speaker", 0))))
        with open(wav_file, "wb") as f:
            f.write(data.to_bytes())
        return wav_file, None   # no phonemes: speech.py makes visemes from the text

    @classproperty
    def available_languages(cls) -> set:
        return set(VOICES)
