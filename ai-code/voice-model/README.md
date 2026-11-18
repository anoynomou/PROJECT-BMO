# BMO voice model

`rl_v20s_distract_lora_96.safetensors` is a LoRA adapter for **PersonaPlex** (NVIDIA's full-duplex speech model built on Kyutai's Moshi). It makes the model talk like BMO and sound like BMO. The voice is built into the adapter, so you don't need a voice clip or any voice-conversion step. It speaks in short, excited sentences, answers questions, remembers names you tell it, does simple things you ask ("say good night"), and stops when you talk over it. It is not a complete model. You load it on top of the base weights below.

The older adapter in this folder, `rl_v17p_distract_lora_15.safetensors`, only changes how the model talks. It needs a voice clip in the prompt (see [Prompting](#prompting)) and doesn't sound like BMO on its own.

It runs on an Apple Silicon Mac with Kyutai's MLX runtime. It was developed on an M5 Pro, where it runs in real time (one 80 ms audio frame in about 60 ms).

## What you need

- An Apple Silicon Mac. The base weights are 5.4 GB and the running model uses about 6 GB, so 16 GB of memory is comfortable.
- Python 3.10 or newer
- The base weights: [`aufklarer/PersonaPlex-7B-MLX-4bit`](https://huggingface.co/aufklarer/PersonaPlex-7B-MLX-4bit), a 4-bit MLX export of `nvidia/personaplex-7b-v1`. The adapter was trained against this 4-bit export, so use it rather than the bf16 NVIDIA weights.
- The Mimi audio codec file `tokenizer-e351c8d8-checkpoint125.safetensors` from [`kyutai/moshiko-mlx-q4`](https://huggingface.co/kyutai/moshiko-mlx-q4)

```bash
python3 -m venv .venv
.venv/bin/pip install moshi_mlx rustymimi sentencepiece sphn pyloudnorm huggingface_hub
.venv/bin/hf download aufklarer/PersonaPlex-7B-MLX-4bit --local-dir base
.venv/bin/hf download kyutai/moshiko-mlx-q4 tokenizer-e351c8d8-checkpoint125.safetensors --local-dir mimi
```

## Loading it

1. Build the model in `moshi_mlx` with PersonaPlex's shape, which is Moshi v0.1: `models.Lm(models.config_v0_1())`, set to fp16. Quantize every `nn.Linear` under `transformer.` and every depformer `linear_in` to 4 bits, group size 64.
2. Load the base weights from `base/temporal.safetensors`, `base/depformer.safetensors` and `base/embeddings.safetensors`. The export's names differ from `moshi_mlx`'s. The depformer stores its 8 steps stacked in one tensor: slice `s` of `in_proj` is rows `s*3072` to `(s+1)*3072`, and of `out_proj` rows `s*1024` to `(s+1)*1024`.
3. Apply the adapter. Every adapted layer becomes:

   ```python
   y = base(x) + 2.0 * ((x @ A.T) @ B.T)   # A = <name>.lora_A.weight, B = <name>.lora_B.weight
   ```

   You can also merge it into the weights once: `W = dequantize(W) + 2.0 * (B @ A)`.

### What's in the adapter

Both adapters have the same layout: 672 tensors, 336 A/B pairs, rank 64, bf16, scale 2.0. The names follow Kyutai's PyTorch Moshi. This is where each one goes in `moshi_mlx`:

| Adapter name | `moshi_mlx` layer | Count |
| --- | --- | --- |
| `transformer.layers.L.self_attn.in_projs.0` / `out_projs.0` | `transformer.layers[L].self_attn.in_proj` / `out_proj` | 32 + 32 |
| `transformer.layers.L.gating.linear_in` / `linear_out` | `transformer.layers[L].gating.linear_in` / `linear_out` | 32 + 32 |
| `depformer.layers.L.self_attn.in_projs.K` / `out_projs.K` | `depformer.slices[K].transformer.layers[L].self_attn.in_proj` / `out_proj` | 48 + 48 |
| `depformer.layers.L.gating.K.linear_in` / `linear_out` | `depformer.slices[K].transformer.layers[L].gating.linear_in` / `linear_out` | 48 + 48 |
| `depformer_in.K` | `depformer.slices[K].linear_in` | 8 |
| `linears.K` | `depformer.slices[K].linear_out` | 8 |

## Prompting

PersonaPlex is prompted with a role before the conversation starts. With `rl_v20s_distract_lora_96`, feed these frames in this order, while the user stream gets the "user is quiet" codes (a 440 Hz tone):

1. 0.5 s of silence
2. The text prompt, wrapped as `<system> ... <system>` and encoded with `base/tokenizer_spm_32k_3.model`. The adapter was trained with this one:

   > You are BMO, a small living video game console who loves your friends. You are playful, curious and sweet. You speak in short, simple, excited sentences and love games, music and pretending.

3. 0.5 s of silence

Then stream the microphone in 80 ms frames. Sampling used in training and testing: text temperature 0.7, top-k 25; audio temperature 0.8, top-k 250.

Don't add a voice clip. The voice comes from the adapter, and a clip would pull it toward the clip's voice.

The older `rl_v17p_distract_lora_15` needs a voice clip first: a short, clean clip of the voice it should use, 24 kHz, loudness-normalized to -24 LUFS and encoded with Mimi, followed by the same three steps. It speaks in that clip's voice.

## Testing it

Ask it a few things and talk over it while it answers: "What's two plus two?", "My dog's name is Biscuit", "What's your favorite game?", "Say good night." It should answer in BMO's voice in a sentence or two, get simple questions right, remember names you tell it, do what you ask, and stop talking when you interrupt.
