# Vídeos mock

Coloque aqui um ou mais ficheiros `.mp4`. No arranque, cada worker escolhe **um** ficheiro ao acaso e faz loop contínuo.

Os MP4 desta pasta entram na imagem Docker (`pedroreis16/vigia-devices`) via `docker-compose/dockerfiles/vigia-devices.dockerfile` — o build falha se a pasta estiver vazia.

Para converter AVI → MP4:

```bash
python ../seed-codes/video_converter.py INPUT=video.avi
```

(ou use o Makefile em `seed-codes/`).
