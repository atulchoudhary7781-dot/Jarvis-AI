# Optional neural voice assets

This project does not package the neural weights or an actor's recordings. When the operator installs/enables the neural runtime, the host obtains three checksum-pinned files from the [onnx-community conversion of Kokoro-82M v1.0](https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/tree/1939ad2a8e416c0acfeecc08a694d14ef25f2231). The model repository identifies the license as [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0).

- Original model: [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M).
- Stock voices, as listed in [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md): Hindi masculine **`hm_omega`**, British English masculine **`bm_george`**.
- Downloaded assets: `onnx/model_quantized.onnx`, `voices/hm_omega.bin`, `voices/bm_george.bin`. Exact revision, expected lengths and SHA-256 digests are in `hologram/voice.py`.
- Runtime: [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) 0.6.1, ONNX Runtime's CPU provider, NumPy and the phonemizer/eSpeak dependencies installed by pip. These third-party packages retain their own upstream licenses.

The renderer and turn-taking code generate an original cinematic hologram. Neither the interface nor the voice is an official Marvel asset or a performer impersonation.
