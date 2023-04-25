
import json
from utils.chatglm.modeling_chatglm import ChatGLMForConditionalGeneration
import torch
import sys

from transformers import AutoTokenizer, GenerationConfig, AutoModel

torch.set_default_tensor_type(torch.cuda.HalfTensor)
model = AutoModel.from_pretrained("THUDM/chatglm-6b", trust_remote_code=True, revision="fdb7a60", cache_dir ="utils/chatglm/model/").cuda().half()
tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm-6b", trust_remote_code=True, revision="fdb7a60", cache_dir ="utils/chatglm/model/")


from peft import get_peft_model, LoraConfig, TaskType, PeftModel

#peft_path = "output/chatglm-lora.pt"

#peft_config = LoraConfig(
#    task_type=TaskType.CAUSAL_LM, inference_mode=True,
#    r=12,
#    lora_alpha=32, lora_dropout=0.1
#)

peft_path = sys.argv[1] if len(sys.argv) > 1 else "./utils/chatglm/output/" 
model = PeftModel.from_pretrained(
       model,
       peft_path,
       torch_dtype=torch.float16,
    )


#model = get_peft_model(model, peft_config)
#model.load_state_dict(torch.load(peft_path), strict=False)
# TODO: check if full precision is necessary
torch.set_default_tensor_type(torch.cuda.FloatTensor)
model.eval()

generation_config = GenerationConfig(
        temperature=0.9,
        top_p=1.1,
        #top_k=150,
        #repetition_penalty=1.1,
        num_beams=1,
        do_sample=True,
)

# 用于给api服务调用
def chatInfer(args):
    try:
        text = args["text"]
        filename = args["filename"]
        with torch.no_grad():
            input_text = f"Context: {text}Answer: " 
            ids = tokenizer([input_text], return_tensors="pt")
            inputs = ids.to("cuda")
            #input_ids = torch.LongTensor([ids]).cuda()
            out = model.generate(
                **inputs,
                max_length=224,
                generation_config=generation_config

            )
            out = out.tolist()[0]
            #print(out)
            decoder_output = tokenizer.decode(out)
            #print(decoder_output)
            out_text = decoder_output.split("Answer: ")[1]
            with open(filename, "w", encoding='UTF8') as f:
                json.dump({"text": out_text, "input": text}, f, ensure_ascii=False)
    except Exception as e:
            print(e)
            return ""

