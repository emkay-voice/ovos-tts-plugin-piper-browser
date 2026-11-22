# ovos-tts-plugin-piper-browser

An [OpenVoiceOS](https://openvoiceos.org) text-to-speech plugin that makes
**Piper** voices on the device itself, in the browser, as WebAssembly. After
the voice has been downloaded once, nothing leaves the device to speak.

It was made for [Emkay](https://github.com/emkay-voice/emkay), OpenVoiceOS in
the browser (Pyodide), and is Emkay's stand-in for
[ovos-tts-plugin-piper](https://github.com/OpenVoiceOS/ovos-tts-plugin-piper),
which needs onnxruntime and espeak-ng and so cannot be installed in a browser.

## How it works

The plugin gives the sentence to the host page's Piper engine and gets a WAV
back. In Emkay that is [`web/piper.js`](https://github.com/emkay-voice/emkay/blob/main/web/piper.js),
in the same Web Worker as OVOS:

- piper-phonemize (espeak-ng) as WebAssembly
  ([@diffusionstudio/piper-wasm](https://www.npmjs.com/package/@diffusionstudio/piper-wasm))
- the voice model on onnxruntime-web
- the voice itself from rhasspy's [piper-voices](https://huggingface.co/rhasspy/piper-voices),
  downloaded the first time and kept in the browser's cache

Until the voice is ready, the plugin raises, and the host speaks with
`tts.fallback_module` instead (Emkay does), so OVOS is never silent while a
voice downloads: about 63 MB, plus 18 MB of espeak-ng data the first time.

A host provides, as a global the worker's Python can reach (`js`):

```js
globalThis.emkayPiper = {
  ready: async (voice) => true | false,   // false: starts the download
  synth: async (text, voice, speaker) => Uint8Array,   // a WAV
};
```

It is called through JSPI (`pyodide.ffi.run_sync`), so the host must run
OVOS where Python can wait for JavaScript.

## Config

```json
"tts": {
  "module": "ovos-tts-plugin-piper-browser",
  "fallback_module": "ovos-tts-plugin-server",
  "ovos-tts-plugin-piper-browser": {"voice": "da_DK-talesyntese-medium"}
}
```

`voice` is a piper-voices name. Without one, the plugin takes the voice for
OVOS' language: English (US and GB), Danish, German, Spanish, French, Italian,
Dutch, Portuguese (Portugal and Brazil), Catalan and Basque. English is
`en_GB-alan-low`, Alan - the voice OpenVoiceOS speaks with by default, and
Mycroft's before it.

The first time, the voice downloads (tens of MB) and the plugin fails that
sentence so `fallback_module` says it. With `"wait_for_download": true` it
waits for the voice instead; for when there is no network to fall back on
(Emkay's "local only" mode sets it).

In the [control panel](https://github.com/OpenVoiceOS/ovos-control-panel) the plugin has a page under Voice: the voice, the speaker and
`wait_for_download`, saved in the section above, and whether it is the voice
in use, with a sentence to hear it (`controlpanel.json`).

## License

Apache-2.0. espeak-ng, inside piper-wasm, is GPL-3.0; each Piper voice has the
licence in its model card.
