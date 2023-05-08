# -*- coding: utf-8 -*-
"""
Created on Sat Apr 15 17:46:03 2023

@author: prane
"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification, RobertaTokenizer, RobertaForSequenceClassification, AutoModelForTokenClassification, DataCollatorForTokenClassification
from sentence_transformers.cross_encoder import CrossEncoder
from sentence_transformers import SentenceTransformer, util
from scipy.special import expit
import torch
from textblob import TextBlob
from functools import reduce

# Enitity types
label_names = ['O', 'B-PER', 'I-PER', 'B-ORG', 'I-ORG', 'B-LOC', 'I-LOC']

# Label to dataset map
label2intent = {
    0: 'chitchat',
    1: 'reddit',
    2: 'empathetic'
}

# Label to topic map
label2topic = {
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
    updated_sentence = []
    for i, w in enumerate(utterance):
        updated_sentence.append(w)
        if w != result[i]:
            updated_sentence.append(result[i])
    return reduce(lambda a, b: a+" "+b, updated_sentence)

# align tokenized words and entity tags with original words.


def wordEntityAlignment(encodings, entities):
    word_ids = encodings.word_ids()
    i = 0
    ents = list(entities.keys())
    print(len(word_ids))
    print(len(ents))
    print(word_ids)
    print(ents)
    updated_entities = {}
    while i < len(ents):
        if word_ids[i] is not None:
            start, end = encodings.word_to_tokens(word_ids[i])
            print(start, end)
            print(ents[start:end])
            word = reduce(lambda a, b: a+b, ents[start:end])
            word = word.replace("#", "")
            updated_entities[word] = entities[ents[start]]
            i += (end-start)
        else:
            i += 1
    return updated_entities


class DialogManager:
    def __init__(self, ):
        # Init tokenizers
        self.topic_tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
        self.intent_tokenizer = RobertaTokenizer.from_pretrained(
            "roberta-base")
        self.ner_tokenizer = AutoTokenizer.from_pretrained(
            "sentientconch/ner_model", use_auth_token='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')

        # Init models
        self.topic_model = AutoModelForSequenceClassification.from_pretrained(
            "sentientconch/topic_classifier", num_labels=6, use_auth_token='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')
        self.intent_model = RobertaForSequenceClassification.from_pretrained(
            'sentientconch/intent_classifier_short_sent', num_labels=3, use_auth_token='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')
        self.ner_model = AutoModelForTokenClassification.from_pretrained(
            "sentientconch/ner_model", use_auth_token='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')

        # bi-encoder to measure sentence similarity
        self.besm = SentenceTransformer('all-mpnet-base-v2')

        self.context = []  # running context, flushed after detecting discontinuity
        self.cache = []  # context cache, flushed at the end of the program, can be used to fetch previous context if elements in running context match an entry in cache
        self.last_input = None  # Last user utterance to track continuity

    # Fetch entites from text.
    def entitiesFromText(self, utterance):
        utterance = spellFix(utterance)
        print(utterance)
        encodings = self.ner_tokenizer(
            [utterance], truncation=True, return_tensors='pt')
        result = self.ner_model(
            encodings["input_ids"], attention_mask=encodings["attention_mask"])[0].argmax(2)
        entities = {}
        for i, enc in enumerate(encodings['input_ids'][0]):
            if enc:
                try:
                    entities[self.ner_tokenizer.decode(
                        enc)] = label_names[result[0][i]]
                except:
                    entities[self.ner_tokenizer.decode(enc)] = label_names[0]
        entities = wordEntityAlignment(encodings, entities)
        print(entities)
        return entities

    # Infer the topic of conversation from user utterance (applies only to Reddit generator)
    def inferTopic(self, utterance):
        encodings = self.topic_tokenizer(
            [utterance], padding=True, truncation=True, return_tensors='pt')
        result = self.topic_model(
            encodings["input_ids"], attention_mask=encodings["attention_mask"])[0].argmax(1)
        return label2topic[result.item()]

    # Infer Intent from user utterance to select the appropriate generator.
    def inferIntent(self, utterance):
        encodings = self.intent_tokenizer(
            [utterance], padding=True, truncation=True, return_tensors='pt')
        # print(self.intent_model(encodings["input_ids"], attention_mask=encodings["attention_mask"])[0])
        result = self.intent_model(
            encodings["input_ids"], attention_mask=encodings["attention_mask"])[0].argmax(1)
        return label2intent[result.item()]

    # Compute similarity between consecutive user utterances
    def biencoder(self, inputs):
        return abs(float(util.cos_sim(self.besm.encode(inputs[0]), self.besm.encode(inputs[1]))[0][0]))

    # Fill, flush running context and cache.
    def track_context(self, text):
        if not self.last_input:
            self.last_input = text
            entities = self.entitiesFromText(text)
            entity_list = [k for k, v in entities.items(
            ) if v != 'O' and '[CLS]' not in k and '[SEP]' not in k]
            print(entity_list)
            list(map(lambda x: self.context.append(x), entity_list))
            return

        related = self.biencoder([text, self.last_input])
        print(related)
        if related >= 0.3:
            entities = self.entitiesFromText(text)
            entity_list = [k for k, v in entities.items(
            ) if v != 'O' and '[CLS]' not in k and '[SEP]' not in k]
            # print(entities)
            list(map(lambda x: self.context.append(x), entity_list))
            # return
        else:
            if len(self.context):
                self.cache.append(self.context)
            self.context = []
            entities = self.entitiesFromText(text)
            entity_list = [k for k, v in entities.items(
            ) if v != 'O' and '[CLS]' not in k and '[SEP]' not in k]
            # print(entities)
            list(map(lambda x: self.context.append(x), entity_list))
            # return None

    def process_user_message(self, utterance):
        intent = self.inferIntent(utterance)
        topic = self.inferTopic(utterance)
        cache = self.cache.copy()
        context = self.context.copy()

        output = {
            "intent": intent,
            "topic": topic,
            "context": context,
            "cache": cache
        }

        self.track_context(utterance)
        return output
