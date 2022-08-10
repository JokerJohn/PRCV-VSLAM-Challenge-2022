# PRCV 2022 setting
from collections import OrderedDict

N_segment = 20

rule_score = OrderedDict() # err(m): score
rule_score[0.05] = 10
rule_score[0.30] = 6
rule_score[0.50] = 3
rule_score[1.00] = 1
