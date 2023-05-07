from transformers import AutoModelWithLMHead, AutoTokenizer
import string
import traceback

def generate_with_question_stop(prompt, model, tokenizer, input_ids, attention_mask, **kwargs):
    beam_outputs = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        **kwargs
    )
    final_outputs = []
    for beam_output in beam_outputs:
        decoded_output = tokenizer.decode(beam_output, skip_special_tokens=True)[len(prompt):]
        try:
            if decoded_output:
                first_sentence = decoded_output.split('.')[1].strip()
                if '?' in first_sentence:
                    continue
                while decoded_output and decoded_output[0] in string.punctuation:
                    decoded_output = decoded_output[1:].lstrip()
                sentences = decoded_output.split('.')
                last_sentence = '.'.join(sentences[:-1]).strip() 
                final_outputs.append(last_sentence)
        except:
            traceback.print_exc()
    return final_outputs


class RedditGenerator:
    def __init__(self, ):
        self.reddit_tokenizer = AutoTokenizer.from_pretrained(
            "skunusot/finetuned-reddit-gpt2", use_auth_token="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")
        self.reddit_model = AutoModelWithLMHead.from_pretrained(
            "skunusot/finetuned-reddit-gpt2", use_auth_token="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")
        
    def generate_response_from_generator(self, input_text):
        inp = self.reddit_tokenizer(input_text, return_tensors="pt")
        input_ids = inp["input_ids"]
        a = inp["attention_mask"]
        beam_outputs = generate_with_question_stop(
			prompt=input_text,
			model=self.reddit_model,
			tokenizer=self.reddit_tokenizer,
			input_ids=input_ids,
			attention_mask=a,
			num_beams=3, 
			early_stopping=True,
			do_sample=True,
			min_length=50,
			num_return_sequences=3, 
			max_length=150 + len(input_ids[0]),
			temperature=1,
			top_k=50,
			top_p=0.95,
			no_repeat_ngram_size=2
		)
        if len(beam_outputs) > 0:
            return beam_outputs[0]  
        else:
            return ""

	
    def generate_response(self, input_text, context):
        return self.generate_response_from_generator(input_text=input_text)
