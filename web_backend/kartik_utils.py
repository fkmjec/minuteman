import os
import re
import json
import numpy as np
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize

CLEAN_PUNC_FILE = "assets/clean_punc.json"
FILLERS_FILE = "assets/fillers.txt"
STOPWORDS_FILE = "assets/stopwords.txt"

def stripp(string):
    list1=[]
    string = string.strip()
    list1[:0]=string
    idx = 0
    cnd = False
    for i in list1:
        if i.isalpha():
            cnd = True
            break
    if cnd:
        while list1[0].isalpha() == False:
            if idx+1 == len(string):
                break
            list1.remove(list1[0])
            idx+=1
        list1 = ''.join(list1)
    else:
        list1 = None

    if list1 == None:
        list1 = ''

    return list1

def replace_apos(ctx):
    ctx = ctx.replace("'ve", " have")
    ctx = ctx.replace("'re", " are")
    ctx = ctx.replace("n't", " not")
    ctx = ctx.replace("'s", " is")
    ctx = ctx.replace("'ll", " will")
    ctx = ctx.replace(" and", ",")
    ctx = ctx.replace(" 's", "")
    if len(ctx)<2:
        ctx = ctx
    else:
        if ctx[0]+ctx[1] == "'s":
            ctx = ctx.replace("'s ", "")
    
    ctx = ctx.replace(",,", ",")
    
    return ctx

def replace_phrases(ctx):
    ctx = ctx.replace("Person", "PERSON")
    ctx = ctx.replace("is going to", "will")
    ctx = ctx.replace("are going to", "will")
    ctx = ctx.replace("are discussing", "discussed")
    ctx = ctx.replace("discuss ", "discussed")
    ctx = ctx.replace("are working", "worked")
    ctx = ctx.replace("is working", "worked")

    return ctx

def clean_punc(ctx):
    puncs = json.load(open(CLEAN_PUNC_FILE, 'r'))
    temp = ''
    while temp!=ctx:
        temp = ctx
        for a,b in zip(puncs['noisy'], puncs['clean']):
            ctx = ctx.replace(a, b)
        
    return ctx

def rem_punc(ctx):
    punc1 = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
    for ele in ctx:
        if ele in punc1:
            ctx = ctx.replace(ele, '')
    return ctx

def rem_multispace(ctx):
    while '  ' in ctx:
        ctx = ctx.replace('  ', ' ')
    return ctx

def rem_repeating(ctx):
    ctx1 = ctx.split(' ')
    for _ in range(len(ctx1)-1):
        if ctx1[_+1].lower() == ctx1[_].lower():
            ctx = ctx.replace(ctx1[_]+' '+ctx1[_+1], ctx1[_])
    
    return ctx

def rem_fillers(ctx):
    fill_file = open(FILLERS_FILE,'r')
    fillers = fill_file.read().split()
    tkns = ctx.split(' ')
    for tkn in tkns:
        if rem_punc(tkn.lower()) in fillers:
            ctx = ctx.replace(tkn, '')
    fill_file.close()
    return ctx

def rem_stopwords(ctx):
    stopfile = open(STOPWORDS_FILE,'r')
    stopwords = stopfile.read().split()
    word_tokens = word_tokenize(ctx)
    filtered_sentence = [w for w in word_tokens if not w.lower() in stopwords]
    ctx = ' '.join(filtered_sentence)
    stopfile.close()
    return ctx

def clean(ctx):
    ctx = rem_repeating(ctx)
    ctx = replace_apos(ctx)
    ctx = rem_multispace(stripp(ctx))
    ctx = rem_fillers(ctx)
    ctx = rem_multispace(stripp(ctx))
    punc2 = '''()-[]{};:"\<>/@#$%^&*_~'''
    for ele in ctx:
        if ele in punc2:
            ctx = ctx.replace(ele, '')
    
    return ctx

def check_context(utterance):
    v = stripp(rem_punc(utterance))
    v = rem_multispace(v)
    v = re.sub(r"[^a-zA-Z0-9]+", ' ', v)

    check = True
    for i in range(1):
        if v == '' or v == ' ' or len(v)<=3:
            check = False
            break
        v = v.split(' ')
        if len(v)<=4:
            check = False
            break
        if len(v)>4 and len(v)<7 and 's' in v:
            check = False
            break
        utterance = stripp(utterance)
        if utterance == None:
            check = False
            break
        if len(utterance) == 1:
            check = False
            break

    return check

def check_req(line1, line2):
    if ('-' in line1) and ('-' in line2):
        st1 = ''
        st2 = ''
        for _ in range(8):
            st1+=line1[_]
            st2+=line2[_]
        if st1 == st2:
            if line1[_+1] == line2[_+1]:
                if line1[_+1]==' ':
                    st3 = st1
                    st4 = st2
                elif line1[_+1]==',':
                    st3 = False
                    st4 = False
                else:
                    st3 = st1+line1[_+1]
                    st4 = st2+line2[_+1]
            else:
                if line1[_+1]=="'" or line2[_+1]=="'":
                    st3 = st1
                    st4 = st2
                else:
                    st3 = False
                    st4 = False
        else:
            st3 = False
            st4 = False
    else:
        st3 = False
        st4 = False

    return st3, st4 

def insert_pronouns(summ1):
    len_sum = len(summ1)
    for line_no, i in enumerate(summ1):
        if '-' in i:
            if len_sum-line_no <= 3:
                rng = len_sum-line_no-1
            else:
                rng = 3
            for k1 in range(rng):
                st1, st2 = check_req(i, summ1[line_no+k1+1])
                if st1:
                    summ1[line_no+k1+1] = summ1[line_no+k1+1].replace(st1, 'They')
                    summ1[line_no+k1+1] = summ1[line_no+k1+1].replace("They's", 'Their')
                    summ1[line_no+k1+1] = summ1[line_no+k1+1].replace("They is", 'They are')
                    summ1[line_no+k1+1] = summ1[line_no+k1+1].replace("They is", 'They are')
                    summ1[line_no+k1+1] = summ1[line_no+k1+1].replace("They has", 'They have')
                    summ1[line_no+k1+1] = summ1[line_no+k1+1].replace("They wants", 'They want')
                    summ1[line_no+k1+1] = summ1[line_no+k1+1].replace("They explains", 'They explain')

    return summ1

def format_summary(s2):
    s3 = ''.join(s2)
    s3 = s3.split('.')
    summ = ['']
    id=0
    summ1 = []
    for i in s3:
        #stripping the spaces
        i = i.replace('  ', ' ')
        if len(i) == 1:
            continue
        if i[0]==' ' and i[1].isalpha():
            i = stripp(i)
        if type(i) == type(None):
            continue
        if i[0] == ' ':
            continue
        i = replace_phrases(i)
        check = re.sub(r"[^a-zA-Z0-9]+", ' ', i)
        check = ''.join(i for i in check if not i.isdigit())
        check = check.replace('  ', ' ')
        check = check.split(' ')
        if len(check)<=6:
            continue

        #formatting
        if i[0] == 'P' and i[1] == 'E':
            summ1.append('-' + i + '.')
        # elif i[0] in ['M','T','O','A'] and (i[1].isalpha()==False):
        #   id+=1
        #   summ.append('')
        #   summ[id] = summ[id] + ' -' + i + '.'
        # elif i[0]=='M' and i[1]=='U':
        #   id+=1
        #   summ.append('')
        #   summ[id] = summ[id] + ' -' + i + '.'
        else:
            summ1.append(i + '.')

    summ1 = insert_pronouns(summ1)
    for i in summ1:
        if i[1] == 'P' and i[2] == 'E':
            id+=1
            summ.append('')
            summ[id] = summ[id] + ' ' + i
        else:
            summ[id] = summ[id] + '\n  ' + i

    if '' in summ:
        summ.remove('')
    summ = '\n'.join(summ)
    
    return summ

def format_summary_(s2, attds):
    # s3 = ''.join(s2)
    s3 = ''.join(s2)
    for p_id, attd in enumerate(attds):
        s3 = s3.replace(attd, 'PERSON'+str(p_id+1))
    s3 = s3.split('.')
    summ = ['']
    id=0
    summ1 = []
    for i in s3:
        #stripping the spaces
        i = i.replace('  ', ' ')
        if len(i) == 1:
            continue
        if i[0]==' ' and i[1].isalpha():
            i = stripp(i)
        if type(i) == type(None):
            continue
        if i[0] == ' ':
            continue
        i = replace_phrases(i)
        check = re.sub(r"[^a-zA-Z0-9]+", ' ', i)
        check = ''.join(i for i in check if not i.isdigit())
        check = check.replace('  ', ' ')
        check = check.split(' ')
        if len(check)<=6:
            continue

        #formatting
        if i[0] == 'P' and i[1] == 'E':
            summ1.append('-' + i + '.')
        # elif i[0] in ['M','T','O','A'] and (i[1].isalpha()==False):
        #   id+=1
        #   summ.append('')
        #   summ[id] = summ[id] + ' -' + i + '.'
        # elif i[0]=='M' and i[1]=='U':
        #   id+=1
        #   summ.append('')
        #   summ[id] = summ[id] + ' -' + i + '.'
        else:
            summ1.append(i + '.')

    summ1 = insert_pronouns(summ1)
    for i in summ1:
        if i[1] == 'P' and i[2] == 'E':
            id+=1
            summ.append('')
            summ[id] = summ[id] + ' ' + i
        else:
            summ[id] = summ[id] + '\n  ' + i

    if '' in summ:
        summ.remove('')
    summ = '\n'.join(summ)
    for p_id, attd in enumerate(attds):
        summ = summ.replace('PERSON'+str(p_id+1), attd)
    
    return summ

def gen_tscs(test_dataset, tokenizer, length):
    with open('/content/drive/MyDrive/Journal/data/{}.json'.format(test_dataset), 'r') as out:
        tscs = json.load(out)

    tscs_preprocessed = []
    for tsc in tscs:
        meeting_id = tsc['meeting_id']
        roles = tsc['roles']
        attendees = (list(set(roles)))
        utterances = tsc['utterances']
        tsc_ = ['']
        i=0
        for role, utterance in zip(roles, utterances):
            utterance = clean(utterance)
            utterance = clean_punc(utterance)
            if check_context(utterance):
                line = role + ': ' + utterance + '\n'
            else:
                continue

            # IF DIALOGUE IS LONGER THAN 'length'
            tokenized_line = tokenizer.encode(line)
            if len(tokenized_line)>=length:
                line_ = line.split('.')
                split_ = len(line_)//2
                line1 = '. '.join(line_[0:split_]) + '.\n'
                line2 = role + ': ' + '. '.join(line_[split_:])
                tokenized_line = [line1, line2]
                for l in tokenized_line:
                    tokenized = tokenizer.encode(tsc_[i]+l)
                    if len(tokenized)>=length:
                        i+=1
                        tsc_.append('')
                        tsc_[i]+=l
                    else:
                        tsc_[i]+=l
            else:
                tokenized = tokenizer.encode(tsc_[i]+line)
                if len(tokenized)>=length:
                    i+=1
                    tsc_.append('')
                    tsc_[i]+=line
                else:
                    tsc_[i]+=line

        tscs_ = dict()
        tscs_['meeting_id'] = meeting_id
        tscs_['attendees'] = attendees
        tscs_['segments'] = tsc_

        tscs_preprocessed.append(tscs_)

    return tscs_preprocessed

def gen_summaries(tscs_preprocessed, summarizer, outdir):
    s2 = []
    filename = []
    meet_no = 1
    for tsc in tscs_preprocessed:
        k = tsc['meeting_id']
        print('{}: {}'.format(meet_no, k))
        k = k + '_summary'
        filename.append(k)
        v = tsc['segments']
        if len(v) < 11:
            section = 2
        elif len(v) < 18:
            section = 4
        elif len(v) < 24: 
            section = 6
        else:
            section = 8
        s1 = ['']
        tsc = v
        id=0
        for i, t1 in enumerate(tsc):
            a1 = summarizer(t1)[0]['summary_text']
            s1[id] = s1[id] + a1 + ' '
            if i%section==0:
                s1.append('')
                id+=1

        s2.append(s1)
        print(s1)

        if 'automin' in outdir:
            s1 = format_summary(s1)
        else:
            s1 = ' '.join(s1)
            s1 = rem_multispace(s1)

        if not os.path.exists(outdir):
            os.mkdir(outdir)

        outfile = open('{}/{}.txt'.format(outdir, k), 'w')
        outfile.write(s1)
        outfile.close()
        meet_no+=1

    return s2, filename

def gen_summaries_(tscs_preprocessed, summarizer, outdir):
    s2 = []
    filename = []
    meet_no = 1
    for tsc in tscs_preprocessed:
        k = tsc['meeting_id']
        attds = tsc['attendees']
        print('{}: {}'.format(meet_no, k))
        k = k + '_summary'
        filename.append(k)
        v = tsc['segments']
        section = round(len(v)/4)
        s1 = ['']
        tsc = v
        # id=0
        for i1, t1 in enumerate(tsc):
            a1 = summarizer(t1)[0]['summary_text']
            # print(i1)
            # print(t1)
            # print(s1)
            s1[i1] = s1[i1] + a1 + ' '
            s1.append('')
            # if i%section==0:
            #     s1.append('')
            #     id+=1

        s2.append(s1)
        print(s1)

        # if 'automin' in outdir:
        #     s1 = format_summary(s1)
        # else:
        #     s1 = ' '.join(s1)
        #     s1 = rem_multispace(s1)

        s1 = format_summary_(s1, attds)

        if not os.path.exists(outdir):
            os.mkdir(outdir)

        outfile = open('{}/{}.txt'.format(outdir, k), 'w')
        outfile.write(s1)
        outfile.close()
        meet_no+=1

    return s2, filename

def gen_summaries2(tscs_preprocessed, summarizer, summarizer_, outdir):
    s2 = []
    s2_= []
    filename = []
    meet_no = 1
    for tsc in tscs_preprocessed:
        k = tsc['meeting_id']
        print('{}: {}'.format(meet_no, k))
        k = k + '_summary'
        filename.append(k)
        v = tsc['segments']
        if len(v) < 11:
            section = 2
        elif len(v) < 18:
            section = 4
        elif len(v) < 24: 
            section = 6
        else:
            section = 8
        s1 = ['']
        s1_ = ''
        tsc = v
        id=0
        for i, t1 in enumerate(tsc):
            a1 = summarizer(t1)[0]['summary_text']
            s1[id] = s1[id] + a1 + ' '

            if i%section==0:
                a2 = summarizer_(s1[-1])[0]['summary_text']
                s1_ = s1_ + a2 + ' '
                s1.append('')
                id+=1
        
        s2.append(s1)
        s2_.append(s1_)
        print(s1)

        if 'automin' in outdir:
            s1 = format_summary(s1)
        else:
            s1 = ' '.join(s1)
            s1 = rem_multispace(s1)

        if not os.path.exists(outdir):
            os.mkdir(outdir)

        outfile = open('{}/{}.txt'.format(outdir, k), 'w')
        outfile.write(s1 + '\n' + s1_)
        outfile.close()
        meet_no+=1

    return s2, s2_, filename

def filter_utterances(utterances, turn_ids):
    filtered = []
    filtered_turns = []
    for id, utt in zip(turn_ids, utterances):
        utt = rem_punc(utt)
        utt = rem_stopwords(utt)
        utt = stripp(rem_punc(utt))
        utt = rem_multispace(utt)
        v = re.sub(r"[^a-zA-Z0-9]+", ' ', utt)
        if v == '' or v == ' ' or len(v)<=3:
            continue
        v = v.split(' ')
        if len(v)<3:
           continue
        if len(v)>3 and len(v)<6 and 's' in v:
            continue

        utt = clean_punc(utt)
        filtered.append(utt)
        filtered_turns.append(id)

    return filtered, filtered_turns
