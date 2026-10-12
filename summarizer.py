import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import pymorphy3

import json

class TicketSummarizer:
    def __init__(self,model_name: str='Qwen/Qwen2.5-3B-Instruct'):
        torch.set_num_threads(2)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.model.eval()
        self.morph = pymorphy3.MorphAnalyzer()


    def summarize(self,text:str) -> dict[str,str]:

        

        messages = [
            {
                'role': 'system',
                'content': (
                    'Ты — AI-аналитик техподдержки. Проанализируй обращение пользователя и верни строго JSON.\n'
                    'Требования к полям:\n'
                    '- "title": развёрнутая фраза от 3 до 6 слов, описывающая суть проблемы (не должна повторять тег).\n'
                    '- "tag": категория или тема обращения в 1-2 слова без мата и эмоций.\n'
                    '- "sentiment": тональность строго одно слово из: positive, neutral, negative.\n'
                    '- "category": тип проблемы строго одно слово из: bug, ui_ux, complaint, feature_request, question, other.\n'
                    '- "priority": уровень срочности строго одно слово из: high (списание денег, взлом, блокировка, критический сбой), mid (обычные ошибки, вопросы работы), low (пожелания, благодарности, мелкие вопросы).\n'
                    'Правило: игнорируй ругательства и оскорбления, фиксируй только суть инцидента.\n'
                    'Формат ответа:\n'
                    '{"title": "описание", "tag": "тема", "sentiment": "neutral", "category": "other", "priority": "mid"}'
                )
            },
            {'role': 'user', 'content': text}
        ]
        
        prompt = self.tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        
        inputs = self.tokenizer(prompt,return_tensors='pt', truncation=True, max_length=512)

    
        with torch.no_grad():
            output = self.model.generate(**inputs,do_sample=False,max_new_tokens=100)
        
        
        
        raw_output = self.tokenizer.decode(output[0][len(inputs.input_ids[0]):], skip_special_tokens=True)

        try:
            start = raw_output.find('{')
            end = raw_output.rfind('}') + 1
            data = json.loads(raw_output[start:end])
            return {
                'title': data.get('title', 'Обращение'),
                'tags': data.get('tag', 'Общее'),
                'sentiment': data.get('sentiment', 'neutral'),
                'category': data.get('category', 'other'),
                'priority': data.get('priority', 'mid')
            }
        except Exception:
            return {
                'title': raw_output.strip(' "\'«»')[:50],
                'tags': 'Обращение',
                'sentiment': 'neutral',
                'category': 'other',
                'priority': 'mid'
            }
    


        

    def extract_tags(self,text:str) -> str:
        words = []
        for w in text.split():
            clean_w = w.strip(".,!&?:;\"'()").lower()
            
            if clean_w:
                words.append(clean_w)
        for i in range(len(words) -1):
            p1 = self.morph.parse(words[i])[0]
            p2 = self.morph.parse(words[i+1])[0]

            if p1.tag.POS == 'NOUN' and p2.tag.POS =='NOUN' and 'gent' in p2.tag:
                return f'{p1.normal_form.capitalize()} {p2.word}'
            elif p1.tag.POS == 'ADJF' and p2.tag.POS == 'NOUN' and 'Apro' not in p1.tag:
                return f'{p1.normal_form.capitalize()} {p2.normal_form}'
            
        for w in words:
            p = self.morph.parse(w)[0]
            if p.tag.POS == "NOUN" and len(w) > 3:
                return p.normal_form.capitalize()
            
        return 'Обращение'
                

        
    def extract(self,text:str) -> dict[str,str]:
        return self.summarize(text)


