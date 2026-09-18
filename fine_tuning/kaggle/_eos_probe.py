from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("/workspace/theology_cpt_v2_merged_hf", trust_remote_code=True)
print("eos", repr(tok.eos_token), tok.eos_token_id)
print("pad", repr(tok.pad_token), tok.pad_token_id)
for t in ["<|im_end|>", "<|endoftext|>", "<EOS_TOKEN>", "<|im_start|>"]:
    tid = tok.convert_tokens_to_ids(t)
    print(t, tid)
