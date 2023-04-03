import io
import logging
import time
from pathlib import Path

import librosa
import matplotlib.pyplot as plt
import numpy as np
import soundfile

from utils.sovits.inference import infer_tool
from utils.sovits.inference import slicer
from utils.sovits.inference.infer_tool import Svc

logging.getLogger('numba').setLevel(logging.WARNING)
chunks_dict = infer_tool.read_temp("./utils/sovits/inference/chunks_temp.json")


def inference(kwargs):

    model_path = kwargs.get('model_path')
    config_path= kwargs.get('config_path')
    clean_names = kwargs.get('clean_names')
    trans = kwargs.get("trans")
    spk_list = kwargs.get("spk_list")
    device = kwargs.get("device", None)
    cluster_model_path = kwargs.get("cluster_model_path", 'logs/44k/kmeans_10000.pt') 
    slice_db=kwargs.get("slice_db", -40)
    wav_format=kwargs.get("wav_format", "flac")
    auto_predict_f0= kwargs.get("auto_predict_f0", False)
    cluster_infer_ratio = kwargs.get("cluster_infer_ratio", 0)
    noice_scale=kwargs.get("noice_scale", 0.4)
    pad_seconds=kwargs.get("pad_seconds", 0.5)

    svc_model = Svc(model_path, config_path, device, cluster_model_path)
    infer_tool.mkdir(["raw", "results"])


    # try:
    raw_audio_path = clean_names
    wav_path = Path(raw_audio_path).with_suffix('.wav')
    chunks = slicer.cut(wav_path, db_thresh=slice_db)
    audio_data, audio_sr = slicer.chunks2audio(wav_path, chunks)

    audio = []
    for (slice_tag, data) in audio_data:
        print(f'#=====segment start, {round(len(data) / audio_sr, 3)}s======')

        length = int(np.ceil(len(data) / audio_sr * svc_model.target_sample))
        if slice_tag:
            print('jump empty segment')
            _audio = np.zeros(length)
        else:
            # padd
            pad_len = int(audio_sr * pad_seconds)
            data = np.concatenate([np.zeros([pad_len]), data, np.zeros([pad_len])])
            raw_path = io.BytesIO()
            soundfile.write(raw_path, data, audio_sr, format="wav")
            raw_path.seek(0)
            out_audio, out_sr = svc_model.infer(spk_list, trans, raw_path,
                                                cluster_infer_ratio=cluster_infer_ratio,
                                                auto_predict_f0=auto_predict_f0,
                                                noice_scale=noice_scale
                                                )
            _audio = out_audio.cpu().numpy()
            pad_len = int(svc_model.target_sample * pad_seconds)
            _audio = _audio[pad_len:-pad_len]

        audio.extend(list(infer_tool.pad_array(_audio, length)))
    key = "auto" if auto_predict_f0 else f"{trans}key"
    cluster_name = "" if cluster_infer_ratio == 0 else f"_{cluster_infer_ratio}"
    res_path = f'./{clean_names.replace("tts_temp", "infer_temp")}_{key}_{spk_list}{cluster_name}.{wav_format}'
    soundfile.write(res_path, audio, svc_model.target_sample, format=wav_format)
    del svc_model
    # except Exception as e:
    #    print(e)
