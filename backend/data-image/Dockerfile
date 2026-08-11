# 语料库数据镜像（scratch 版，无需外部基础镜像）
#
# 用法：
#   1. 在宿主机将语料库 JSON 压缩（推荐 gzip -9，1.8GB → ~400MB）：
#        gzip -9 -k recipe_corpus_full.json      # 生成 recipe_corpus_full.json.gz
#      或 Python：python -c "import gzip,shutil;
#                with open('recipe_corpus_full.json','rb') as f_in, \
#                     gzip.open('recipe_corpus_full.json.gz','wb',compresslevel=9) as f_out:
#                    shutil.copyfileobj(f_in, f_out)"
#   2. 将 .gz 放入本目录，然后构建：
#        docker build -t cookbook/corpus:latest .
#
# 产物：镜像内 /data/recipe_corpus_full.json.gz
FROM scratch

COPY recipe_corpus_full.json.gz /data/recipe_corpus_full.json.gz
