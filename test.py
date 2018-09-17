from load_MITBIH import *

DS1 = [101]

#load_signal(DS1,winL,winR,1)
winL=90
winR=90
do_preprocess=True
use_weight_class=True
maxRR=False
use_RR=False
norm_RR=False
compute_morph={'wvlt'}
oversamp_method = ''
reduced_DS = False
leads_flag = [1,0]
db_path = 'dataset/mitdb/m_learning/scikit/'

load_mit_db('DS1', winL, winR, do_preprocess, maxRR, use_RR, norm_RR, compute_morph, db_path, reduced_DS, leads_flag) # for testing
