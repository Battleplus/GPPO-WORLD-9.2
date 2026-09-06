# Adapter consumption report

Demo B 使用 `EAWM-GPPO` seed 1101、step 50000 的历史 adapter checkpoint。checkpoint SHA-256 为 `bc4e5e9cc1741892ced68f6166845d6c0c5e63452d852c928354669156e1a1bd`；绑定 world SHA-256 为 `eb8c13dd822f27511ed892091833b1fd5b8d69ed28b044ec47a7e34a68b19cf`；校准 SHA-256 为 `a77f2a38ff99bc63996af343e2218ebaea84e943448fab15618454fc1265272d`。

服务器 B 证据：100 held-out tapes、635 decisions、577 valid Shadow、58 fallback、487 次 `latent_adapter_used=true`。其余首决策或 fallback/不匹配情形保持 zero/base path。adapter 消费发生在历史 EAWM-GPPO policy 中；A 的 S3 pure GPPO 明确为 `context_consumed=false`，两者没有被混写。
