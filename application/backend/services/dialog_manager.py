# -*- coding: utf-8 -*-
"""
Created on Sat Apr 15 17:46:03 2023

@author: prane
"""
from transformers import AutoTokenizer, DistilBertForSequenceClassification, AutoModelForSequenceClassification, RobertaTokenizer, RobertaForSequenceClassification, AutoModelForTokenClassification, DataCollatorForTokenClassification
from sentence_transformers.cross_encoder import CrossEncoder
from sentence_transformers import SentenceTransformer, util
from scipy.special import expit
import torch
from textblob import TextBlob
from functools import reduce

# Enitity types
label_names = ['O', 'B-PER', 'I-PER', 'B-ORG', 'I-ORG', 'B-LOC', 'I-LOC']

# Label to dataset map
label2intent={
    0: 'chitchat',
    1: 'reddit',
    2: 'empathetic'
    }

# Label to topic map
label2topic={
    0: 'education',
    1: 'politics',
    2: 'healthcare',
    3: 'environment',
    4: 'technology',
    5: 'unknown'
    }    

# correct spelling and combine corrected spelling with the original spelling.
def spellFix(utterance):
    sentence = TextBlob(utterance)
    result = sentence.correct()
    utterance = utterance.split(" ")
    result = result.split(" ")
    updated_sentence=[]
    for i,w in enumerate(utterance):
        updated_sentence.append(w)
        if w != result[i]:
            updated_sentence.append(result[i])
    return reduce(lambda a,b: a+" "+b,updated_sentence) 

# align tokenized words and entity tags with original words.
def wordEntityAlignment(encodings, entities):
    word_ids = encodings.word_ids()
    i=0
    ents = list(entities.keys())
    # print(entities.values())
    # print(len(word_ids))
    # print(len(ents))
    # print(word_ids)
    # print(ents)
    updated_entities = {}
    entity_spans = {}
    while i < len(ents):
        if word_ids[i] is not None:
            start, end = encodings.word_to_tokens(word_ids[i])
            # print(start,end)
            # print(ents[start:end])
            word = reduce(lambda a,b:a+b, ents[start:end])
            word = word.replace("#","")
            updated_entities[word] = entities[ents[start]]
            i+=(end-start)
        else:    
            i+=1
    # for i, w in enumerate(updated_entities.keys()):
    # print(updated_entities)
    i = 0
    words = list(updated_entities.keys())
    while i < len(words):
        w = words[i]
        # print("word "+w)
        span_word = w
        if "I" in updated_entities[w]:
            i+=1
            continue
        if updated_entities[w] == 'O':
            i+=1
            continue
        for j, nw in enumerate(words[i+1:]):
            print("next_word "+nw)
            # print(updated_entities[nw][-3:])
            # print(updated_entities[w])
            if updated_entities[nw][-3:] == updated_entities[w][-3:]:
                span_word+=(" "+nw)
                # print(span_word)
                # continue
            else:
                break
        i=i+j+2
        # print(f"i is {i}")
        entity_spans[span_word] = updated_entities[w][-3:]
    
    # filtered_span = {}
    # for k,v in entity_spans.keys():
    #     if v
    return entity_spans


class DialogManager:
    def __init__(self, ):
        # Init tokenizers
        self.topic_tokenizer =  AutoTokenizer.from_pretrained("bert-base-cased")
        # self.intent_tokenizer = RobertaTokenizer.from_pretrained("roberta-base")
        self.intent_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        self.ner_tokenizer =  AutoTokenizer.from_pretrained("sentientconch/ner_model", use_auth_token='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')
        
        # Init models
        self.topic_model = AutoModelForSequenceClassification.from_pretrained("sentientconch/topic_classifier", num_labels=6, use_auth_token='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')
        # self.intent_model = RobertaForSequenceClassification.from_pretrained('sentientconch/intent_classifier_short_sent', num_labels=3, use_auth_token='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')
        self.intent_model = DistilBertForSequenceClassification.from_pretrained("sentientconch/intent_classifier_large", num_labels=3, use_auth_token='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')
        self.ner_model = AutoModelForTokenClassification.from_pretrained("sentientconch/ner_model", use_auth_token='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')
        
        # bi-encoder to measure sentence similarity
        self.besm = SentenceTransformer('all-mpnet-base-v2')
        
        self.context=[] # running context, flushed after detecting discontinuity
        self.cache=[] # context cache, flushed at the end of the program, can be used to fetch previous context if elements in running context match an entry in cache
        self.last_input = None # Last user utterance to track continuity            
        
    # Fetch entites from text. 
    def entitiesFromText(self, utterance):
        # utterance = spellFix(utterance)
        # print(utterance)
        encodings = self.ner_tokenizer([utterance], truncation=True, return_tensors='pt')
        result = self.ner_model(encodings["input_ids"], attention_mask=encodings["attention_mask"])[0].argmax(2)
        # print(result)
        entities = {}
        for i,enc in enumerate(encodings['input_ids'][0]):
            if enc:
                try:
                    entities[self.ner_tokenizer.decode(enc)] = label_names[result[0][i]]
                except:
                    entities[self.ner_tokenizer.decode(enc)] = label_names[0]
        entities = wordEntityAlignment(encodings, entities)
        # print(entities)
        return entities
    
    # Infer the topic of conversation from user utterance (applies only to Reddit generator)
    def inferTopic(self, utterance):
        encodings = self.topic_tokenizer([utterance], padding=True, truncation=True, return_tensors='pt')
        result = self.topic_model(encodings["input_ids"], attention_mask=encodings["attention_mask"])[0].argmax(1)
        return label2topic[result.item()]
    
    # Infer Intent from user utterance to select the appropriate generator.
    def inferIntent(self, utterance):
        encodings = self.intent_tokenizer([utterance], padding=True, truncation=True, return_tensors='pt')
        # print(self.intent_model(encodings["input_ids"], attention_mask=encodings["attention_mask"])[0])
        logits = self.intent_model(encodings["input_ids"], attention_mask=encodings["attention_mask"])[0]
        result = logits.argmax(1)
        print(logits)
        probs = logits.softmax(1)
        result = self.intent_model(encodings["input_ids"], attention_mask=encodings["attention_mask"])[0].argmax(1)
        return label2intent[result.item()], probs[0].tolist()
    
    # Compute similarity between consecutive user utterances
    def biencoder(self, inputs):
        return abs(float(util.cos_sim(self.besm.encode(inputs[0]),self.besm.encode(inputs[1]))[0][0]))
    
    # Fill, flush running context and cache.
    def track_context(self, text):
        if not self.last_input:
            self.last_input = text
            entities = self.entitiesFromText(text)
            entity_list = [k for k,v in entities.items() if v != 'O' and '[CLS]' not in k and '[SEP]' not in k]
            # print(entity_list)
            list(map(lambda x: self.context.append(x), entity_list))
            return
        
        related = self.biencoder([text, self.last_input])
        print(related)
        if related >= 0.3:
            entities = self.entitiesFromText(text)
            entity_list = [k for k,v in entities.items() if v != 'O' and '[CLS]' not in k and '[SEP]' not in k]
            # print(entities)
            list(map(lambda x: self.context.append(x), entity_list))
            # return 
        else:
            if len(self.context): self.cache.append(self.context)
            self.context = []
            entities = self.entitiesFromText(text)
            entity_list = [k for k,v in entities.items() if v != 'O' and '[CLS]' not in k and '[SEP]' not in k]
            # print(entities)
            list(map(lambda x: self.context.append(x), entity_list))
            # return None


if __name__ == "__main__":
    dm = DialogManager()
    while 1:
        utterance = input("prompt: \n")
        i, ip = dm.inferIntent(utterance)
        t = dm.inferTopic(utterance)
        dm.track_context(utterance)
        print(dm.context)
        print(dm.cache)
        print(i)
        print(ip)
        print(t)
    
    