import os
import sys
import time

import azure.cognitiveservices.speech as speechsdk


# 第一步，产生基础的tts语音音频文件
def tts_azure(tts_config, txt, audioOuputPath='audio_temp/tts_temp/'):

    audioOuputFile = audioOuputPath + str(int(time.time())) + '.wav'

    languageCode = 'zh-CN'
    voicName = 'zh-CN-XiaoxuanNeural'
    speakingRate = '-15%'
    pitch = '-10%'
    voiceStyle = 'gentle'

    head1 = f'<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="{languageCode}">'
    head2 = f'<voice name="{voicName}">'
    head3 =f'<mstts:express-as style="{voiceStyle}">'
    head4 = f'<prosody rate="{speakingRate}" pitch="{pitch}">'
    tail= '</prosody></mstts:express-as></voice></speak>'

    ssml = head1 + head2 + head3 + head4 + txt + tail
    print('this is the ssml======================================')
    print(ssml)
    print('end ssml======================================')
    print()

    speech_config = speechsdk.SpeechConfig(subscription=tts_config["speech_key"], region=tts_config["speech_region"])
    audio_config = speechsdk.AudioConfig(filename=audioOuputFile)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    synthesizer.speak_ssml_async(ssml).get()
    
    return audioOuputFile

if __name__ == '__main__':
    tts_config = {
        "speech_key": "49a539a960dc4a10ba5f87a67009088d",
        "speech_region": "eastasia"
    }
    txt = 'We hope someday, having solved the problems we face, to join a community of galactic civilizations. This record represents our hope and our determination, and our good will in a vast and awesome universe.'
    audioOuputFile = tts_azure(tts_config, txt)